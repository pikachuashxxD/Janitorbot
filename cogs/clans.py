import discord
from discord import app_commands, ui
from discord.ext import commands
import json
import os
from utils.database import update_config, get_config

# --- CLAN DATABASE MANAGER ---
CLAN_FILE = "clans.json"

def load_clans():
    if not os.path.exists(CLAN_FILE):
        return {}
    with open(CLAN_FILE, "r") as f:
        return json.load(f)

def save_clans(data):
    with open(CLAN_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- HELPER: SEND LOG TO CLAN-LOGS CHANNEL ---
async def send_clan_log(guild, title, description, color):
    conf = get_config(guild.id)
    log_channel_id = conf.get("clan_log_channel")
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if channel:
            embed = discord.Embed(
                title=title, 
                description=description, 
                color=color,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Clan System Log")
            await channel.send(embed=embed)

# ======================================================
# 1. VIEW: CLAN CREATION (Admins)
# ======================================================
class ClanCreationView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def get_details_from_embed(self, interaction):
        embed = interaction.message.embeds[0]
        try:
            footer_text = embed.footer.text
            leader_id = int(footer_text.split(": ")[1])
        except:
            leader_id = 0
        
        clan_name = "Unknown"
        for field in embed.fields:
            if field.name == "Clan Name":
                clan_name = field.value.replace("**", "") 
                break
        return leader_id, clan_name

    @ui.button(label="✅ Approve", style=discord.ButtonStyle.green, custom_id="clan_req:approve")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        leader_id, clan_name = await self.get_details_from_embed(interaction)
        guild = interaction.guild
        
        conf = get_config(guild.id)
        cat_id = conf.get("clan_category")
        category = guild.get_channel(cat_id)
        leader = guild.get_member(leader_id)
        
        if not category:
            return await interaction.response.send_message("❌ Clan Category not found. Run setup again.", ephemeral=True)

        # 1. Create Role
        try:
            clan_role = await guild.create_role(name=clan_name, reason=f"Clan Created by {interaction.user.name}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I don't have permission to create roles!", ephemeral=True)

        # 2. Create Channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            leader: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True) if leader else None,
            clan_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel_name = clan_name.lower().replace(" ", "-")
        channel = await guild.create_text_channel(name=f"🛡️・{channel_name}", category=category, overwrites=overwrites)

        # 3. Assign Role & Notify
        if leader:
            try:
                await leader.add_roles(clan_role)
            except:
                await channel.send("⚠️ I could not give the leader the clan role (My role might be below theirs).")
            
            await channel.send(f"{leader.mention}, your clan **{clan_name}** is ready! 🎉\nRole: {clan_role.mention}")

        # 4. Save to DB
        clans = load_clans()
        clans[str(channel.id)] = {
            "name": clan_name,
            "leader_id": leader_id,
            "channel_id": channel.id,
            "role_id": clan_role.id,
            "members": [leader_id]
        }
        save_clans(clans)

        # 5. Update Embed & Log
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Clan Approved"
        embed.add_field(name="Approved By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"Created {channel.mention}", ephemeral=True)

        await send_clan_log(guild, "🛡️ Clan Created", 
            f"**Name:** {clan_name}\n**Leader:** {leader.mention if leader else 'Unknown'}\n**Approved By:** {interaction.user.mention}", 
            discord.Color.green())

    @ui.button(label="❌ Reject", style=discord.ButtonStyle.red, custom_id="clan_req:reject")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        leader_id, clan_name = await self.get_details_from_embed(interaction)
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Clan Rejected"
        embed.add_field(name="Rejected By", value=interaction.user.mention, inline=False)
        
        leader = interaction.guild.get_member(leader_id)
        if leader:
            try:
                await leader.send(f"❌ Your request to create the clan **{clan_name}** was rejected.")
            except:
                pass

        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Request rejected.", ephemeral=True)

        await send_clan_log(interaction.guild, "🚫 Clan Rejected", 
            f"**Name:** {clan_name}\n**Applicant:** {leader.mention if leader else 'Unknown'}\n**Rejected By:** {interaction.user.mention}", 
            discord.Color.red())


# ======================================================
# 2. VIEW: MEMBER APPLICATION (Leaders)
# ======================================================
class MemberApplicationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="✅ Accept", style=discord.ButtonStyle.green, custom_id="clan_app:accept")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if not clan_data:
            return await interaction.response.send_message("❌ Error: Clan data not found.", ephemeral=True)

        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can accept members!", ephemeral=True)

        embed = interaction.message.embeds[0]
        try:
            applicant_id = int(embed.footer.text.split(": ")[1])
            applicant = interaction.guild.get_member(applicant_id)
        except:
            applicant = None

        if applicant:
            await interaction.channel.set_permissions(applicant, read_messages=True, send_messages=True)
            
            role_id = clan_data.get("role_id")
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    try:
                        await applicant.add_roles(role)
                    except:
                        pass

            await interaction.channel.send(f"Welcome {applicant.mention} to **{clan_data['name']}**! 🎉")
            
            if applicant.id not in clan_data["members"]:
                clan_data["members"].append(applicant.id)
                save_clans(clans)

            await send_clan_log(interaction.guild, "👤 Member Joined Clan", 
                f"**User:** {applicant.mention}\n**Clan:** {clan_data['name']}\n**Accepted By:** {interaction.user.mention}", 
                discord.Color.blue())
        else:
            await interaction.channel.send("User left the server or cannot be found.")

        await interaction.message.delete()

    @ui.button(label="❌ Deny", style=discord.ButtonStyle.red, custom_id="clan_app:deny")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can deny members!", ephemeral=True)

        embed = interaction.message.embeds[0]
        try:
            applicant_id = int(embed.footer.text.split(": ")[1])
            applicant = interaction.guild.get_member(applicant_id)
            if applicant:
                try:
                    await applicant.send(f"❌ Your application to join **{clan_data['name']}** was denied.")
                except:
                    pass
        except:
            pass

        await interaction.message.delete()
        await interaction.response.send_message("Application denied.", ephemeral=True)

# ======================================================
# 3. VIEW: OWNERSHIP TRANSFER (Admins)
# ======================================================
class ClanTransferView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def get_transfer_details(self, interaction):
        embed = interaction.message.embeds[0]
        # Footer Format: "Clan Channel: 12345 | New Leader: 67890"
        parts = embed.footer.text.split(" | ")
        channel_id = str(parts[0].split(": ")[1])
        new_leader_id = int(parts[1].split(": ")[1])
        return channel_id, new_leader_id

    @ui.button(label="✅ Approve Transfer", style=discord.ButtonStyle.green, custom_id="clan_transfer:approve")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        channel_id_str, new_leader_id = await self.get_transfer_details(interaction)
        clans = load_clans()
        
        if channel_id_str not in clans:
            return await interaction.response.send_message("❌ Clan not found (Channel might be deleted).", ephemeral=True)

        clan_data = clans[channel_id_str]
        guild = interaction.guild
        
        new_leader = guild.get_member(new_leader_id)
        old_leader = guild.get_member(clan_data["leader_id"])
        clan_channel = guild.get_channel(int(channel_id_str))

        if not new_leader:
            return await interaction.response.send_message("❌ New leader has left the server.", ephemeral=True)

        # 1. Update Permissions
        if clan_channel:
            if old_leader:
                await clan_channel.set_permissions(old_leader, read_messages=True, send_messages=True, mention_everyone=False)
            await clan_channel.set_permissions(new_leader, read_messages=True, send_messages=True, mention_everyone=True)
            await clan_channel.send(f"👑 **Ownership Transferred!**\n{new_leader.mention} is now the Leader.")

        # 2. Update DB
        clan_data["leader_id"] = new_leader_id
        save_clans(clans)

        # 3. Update Admin Log
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Transfer Approved"
        embed.add_field(name="Approved By", value=interaction.user.mention, inline=False)
        await interaction.message.edit(embed=embed, view=None)
        
        await interaction.response.send_message("Ownership transferred.", ephemeral=True)

        await send_clan_log(guild, "👑 Ownership Transferred", 
            f"**Clan:** {clan_data['name']}\n**Old Leader:** {old_leader.mention if old_leader else 'Unknown'}\n**New Leader:** {new_leader.mention}", 
            discord.Color.gold())

    @ui.button(label="❌ Reject Transfer", style=discord.ButtonStyle.red, custom_id="clan_transfer:reject")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Transfer Rejected"
        embed.add_field(name="Rejected By", value=interaction.user.mention, inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Transfer rejected.", ephemeral=True)


# ======================================================
# 4. MAIN COG
# ======================================================
class ClanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(ClanCreationView(bot))
        self.bot.add_view(MemberApplicationView())
        self.bot.add_view(ClanTransferView(bot))

    # --- AUTOCOMPLETE ---
    async def clan_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        clans = load_clans()
        choices = []
        for data in clans.values():
            name = data["name"]
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]

    # --- SETUP ---
    @app_commands.command(name="setup_clan_system", description="Auto-create categories and channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_clan_system(self, interaction: discord.Interaction, leader_role: discord.Role):
        guild = interaction.guild
        await interaction.response.defer()

        admin_cat = await guild.create_category("🔒 Clan Admin Logs")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            leader_role: discord.PermissionOverwrite(read_messages=False)
        }
        approve_channel = await guild.create_text_channel("📜・clan-approvals", category=admin_cat, overwrites=overwrites)
        log_channel = await guild.create_text_channel("qh・clan-logs", category=admin_cat, overwrites=overwrites)
        clan_cat = await guild.create_category("🛡️ Clans")

        update_config(guild.id, "clan_leader_role", leader_role.id)
        update_config(guild.id, "clan_approve_channel", approve_channel.id)
        update_config(guild.id, "clan_log_channel", log_channel.id)
        update_config(guild.id, "clan_category", clan_cat.id)

        embed = discord.Embed(title="✅ Clan System Setup Complete", color=0x2ecc71)
        embed.add_field(name="Leader Role", value=leader_role.mention)
        embed.add_field(name="Approvals Channel", value=approve_channel.mention)
        embed.add_field(name="Logs Channel", value=log_channel.mention)
        await interaction.followup.send(embed=embed)

    # --- CREATE ---
    @app_commands.command(name="create_clan", description="Request to create a new clan")
    async def create_clan(self, interaction: discord.Interaction, name: str, description: str):
        conf = get_config(interaction.guild_id)
        role_id = conf.get("clan_leader_role")
        
        if not role_id: 
            return await interaction.response.send_message("❌ Clan system not setup.", ephemeral=True)
        
        role = interaction.guild.get_role(role_id)
        if role not in interaction.user.roles:
            return await interaction.response.send_message(f"❌ You need the {role.mention} role to create a clan.", ephemeral=True)

        approve_channel_id = conf.get("clan_approve_channel")
        channel = interaction.guild.get_channel(approve_channel_id)

        embed = discord.Embed(title="🛡️ New Clan Request", color=0xf1c40f)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Clan Name", value=f"**{name}**", inline=True)
        embed.add_field(name="Proposed Leader", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Description", value=description, inline=False)
        embed.set_footer(text=f"Leader ID: {interaction.user.id}")

        await channel.send(embed=embed, view=ClanCreationView(self.bot))
        await interaction.response.send_message("✅ Request Sent!", ephemeral=True)

    # --- APPLY ---
    @app_commands.command(name="apply_clan", description="Apply to join a specific clan")
    @app_commands.autocomplete(clan_name=clan_name_autocomplete)
    async def apply_clan(self, interaction: discord.Interaction, clan_name: str, message: str):
        clans = load_clans()
        target_clan = None
        for data in clans.values():
            if data["name"].lower() == clan_name.lower():
                target_clan = data
                break
        
        if not target_clan: 
            return await interaction.response.send_message("❌ Clan not found.", ephemeral=True)
        
        if interaction.user.id in target_clan["members"]: 
            return await interaction.response.send_message("❌ You are already in this clan.", ephemeral=True)

        clan_channel = interaction.guild.get_channel(target_clan["channel_id"])
        
        if not clan_channel:
            return await interaction.response.send_message(f"❌ Channel for **{clan_name}** deleted.", ephemeral=True)

        embed = discord.Embed(title="📩 New Membership Application", color=0x3498db)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Applicant", value=interaction.user.mention, inline=True)
        embed.add_field(name="Message", value=message, inline=False)
        embed.set_footer(text=f"Applicant ID: {interaction.user.id}")
        
        await clan_channel.send(content=f"<@{target_clan['leader_id']}>", embed=embed, view=MemberApplicationView())
        await interaction.response.send_message(f"✅ Application sent to **{clan_name}**!", ephemeral=True)

    # --- LEAVE ---
    @app_commands.command(name="leave_clan", description="Leave your current clan")
    async def leave_clan(self, interaction: discord.Interaction):
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)
        if channel_id_str not in clans: 
            return await interaction.response.send_message("❌ Run this inside your clan channel.", ephemeral=True)

        clan_data = clans[channel_id_str]
        if interaction.user.id == clan_data["leader_id"]: 
            return await interaction.response.send_message("❌ Leaders cannot leave. Use `/disband_clan` or `/transfer_ownership`.", ephemeral=True)

        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        
        role_id = clan_data.get("role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role: 
                try: await interaction.user.remove_roles(role)
                except: pass

        clan_data["members"].remove(interaction.user.id)
        save_clans(clans)
        await interaction.response.send_message(f"{interaction.user.mention} left the clan.", ephemeral=False)

        await send_clan_log(interaction.guild, "🚪 Member Left Clan", 
            f"**User:** {interaction.user.mention}\n**Clan:** {clan_data['name']}", 
            discord.Color.orange())

    # --- DISBAND ---
    @app_commands.command(name="disband_clan", description="⚠️ Delete your clan permanently (Leader Only)")
    async def disband_clan(self, interaction: discord.Interaction):
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)
        
        if channel_id_str not in clans:
            return await interaction.response.send_message("❌ Run this inside your clan channel.", ephemeral=True)
            
        clan_data = clans[channel_id_str]
        
        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Only the **Clan Leader** can disband the clan.", ephemeral=True)

        await interaction.response.send_message("⚠️ Disbanding clan... Goodbye!", ephemeral=True)

        role_id = clan_data.get("role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                try: await role.delete(reason="Clan Disbanded")
                except: pass 

        await send_clan_log(interaction.guild, "🗑️ Clan Disbanded", 
            f"**Clan:** {clan_data['name']}\n**Action By:** {interaction.user.mention}", 
            discord.Color.dark_red())

        del clans[channel_id_str]
        save_clans(clans)
        await interaction.channel.delete(reason="Clan Disbanded")

    # --- TRANSFER ---
    @app_commands.command(name="transfer_ownership", description="Transfer leadership to another member")
    @app_commands.describe(new_leader="The member to make the new Leader")
    async def transfer_ownership(self, interaction: discord.Interaction, new_leader: discord.Member):
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)

        if channel_id_str not in clans: return await interaction.response.send_message("❌ Run this inside your clan channel.", ephemeral=True)
        clan_data = clans[channel_id_str]

        if interaction.user.id != clan_data["leader_id"]:
            return await interaction.response.send_message("❌ Only the **Clan Leader** can transfer ownership.", ephemeral=True)

        if new_leader.id not in clan_data["members"]:
            return await interaction.response.send_message("❌ The new leader must be a member of this clan first!", ephemeral=True)

        # Send Request to Admin
        conf = get_config(interaction.guild_id)
        approve_id = conf.get("clan_approve_channel")
        approve_channel = interaction.guild.get_channel(approve_id)

        if not approve_channel:
             return await interaction.response.send_message("❌ Admin approval channel not found.", ephemeral=True)

        embed = discord.Embed(title="👑 Ownership Transfer Request", color=0xf1c40f)
        embed.add_field(name="Clan Name", value=f"**{clan_data['name']}**", inline=True)
        embed.add_field(name="Current Leader", value=interaction.user.mention, inline=True)
        embed.add_field(name="New Leader", value=new_leader.mention, inline=True)
        
        embed.set_footer(text=f"Clan Channel: {channel_id_str} | New Leader: {new_leader.id}")

        await approve_channel.send(embed=embed, view=ClanTransferView(self.bot))
        await interaction.response.send_message("✅ **Transfer Request Sent!** Admins will review it soon.", ephemeral=True)

    # --- KICK ---
    @app_commands.command(name="clan_kick", description="Kick a member from the clan (Leader Only)")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    async def clan_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)

        if channel_id_str not in clans:
            return await interaction.response.send_message("❌ Run this inside your clan channel.", ephemeral=True)
        
        clan_data = clans[channel_id_str]
        
        if interaction.user.id != clan_data["leader_id"]:
            return await interaction.response.send_message("❌ Only the **Leader** can kick members.", ephemeral=True)

        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot kick yourself.", ephemeral=True)

        if member.id not in clan_data["members"]:
            return await interaction.response.send_message("❌ That user is not in your clan.", ephemeral=True)

        await interaction.channel.set_permissions(member, overwrite=None)
        
        role_id = clan_data.get("role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role: 
                try: await member.remove_roles(role)
                except: pass

        clan_data["members"].remove(member.id)
        save_clans(clans)

        await interaction.response.send_message(f"👢 **{member.display_name}** has been kicked from the clan.\n**Reason:** {reason}")

        await send_clan_log(interaction.guild, "👢 Member Kicked", 
            f"**Clan:** {clan_data['name']}\n**Kicked:** {member.mention}\n**By:** {interaction.user.mention}\n**Reason:** {reason}", 
            discord.Color.red())

    # --- CLAN INFO ---
    @app_commands.command(name="clan_info", description="View details about the current clan")
    async def clan_info(self, interaction: discord.Interaction):
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)

        if channel_id_str not in clans:
            return await interaction.response.send_message("❌ This is not a clan channel.", ephemeral=True)

        clan_data = clans[channel_id_str]
        leader = interaction.guild.get_member(clan_data["leader_id"])
        
        member_names = []
        for uid in clan_data["members"]:
            mem = interaction.guild.get_member(uid)
            if mem: member_names.append(mem.display_name)
            else: member_names.append(f"Unknown ({uid})")

        embed = discord.Embed(title=f"🛡️ Clan: {clan_data['name']}", color=0x3498db)
        embed.set_thumbnail(url=leader.display_avatar.url if leader else None)
        embed.add_field(name="👑 Leader", value=leader.mention if leader else "Unknown", inline=True)
        embed.add_field(name="👥 Members", value=f"{len(clan_data['members'])}", inline=True)
        embed.add_field(name="📜 Member List", value=", ".join(member_names) if member_names else "None", inline=False)

        await interaction.response.send_message(embed=embed)

    # --- NEW: CLAN LIST (LEADERBOARD) ---
    @app_commands.command(name="clan_list", description="View the top 10 clans by size")
    async def clan_list(self, interaction: discord.Interaction):
        clans = load_clans()
        
        if not clans:
            return await interaction.response.send_message("❌ No clans have been created yet.", ephemeral=True)
        
        # Sort clans by number of members (descending)
        sorted_clans = sorted(clans.values(), key=lambda x: len(x['members']), reverse=True)
        
        description = ""
        for i, clan_data in enumerate(sorted_clans[:10], 1):
            leader_name = "Unknown"
            # Try to fetch leader name from cache
            leader = interaction.guild.get_member(clan_data["leader_id"])
            if leader: leader_name = leader.display_name
            
            description += f"**{i}. {clan_data['name']}**\n👑 Leader: {leader_name} | 👥 Members: {len(clan_data['members'])}\n\n"
        
        embed = discord.Embed(title="🏆 Top Clans Leaderboard", description=description, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanSystem(bot))
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
            embed = discord.Embed(title=title, description=description, color=color)
            embed.set_footer(text=f"Time: {discord.utils.format_dt(discord.utils.utcnow(), 't')}")
            await channel.send(embed=embed)

# ======================================================
# 1. PERSISTENT VIEW: CLAN CREATION (Admins)
# ======================================================
class ClanCreationView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def get_details_from_embed(self, interaction):
        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text
        leader_id = int(footer_text.split(": ")[1])
        clan_name = embed.fields[0].value.replace("*", "")
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

        # 1. CREATE ROLE
        try:
            clan_role = await guild.create_role(name=clan_name, reason=f"Clan Created by {interaction.user.name}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I don't have permission to create roles!", ephemeral=True)

        # 2. CREATE CHANNEL
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            leader: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True) if leader else None,
            clan_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel_name = clan_name.lower().replace(" ", "-")
        channel = await guild.create_text_channel(name=f"🛡️・{channel_name}", category=category, overwrites=overwrites)

        # 3. ASSIGN ROLE TO LEADER
        if leader:
            try:
                await leader.add_roles(clan_role)
            except:
                await channel.send("⚠️ I could not give the leader the clan role (My role might be below theirs).")

        # 4. SAVE TO DB
        clans = load_clans()
        clans[str(channel.id)] = {
            "name": clan_name,
            "leader_id": leader_id,
            "channel_id": channel.id,
            "role_id": clan_role.id,
            "members": [leader_id]
        }
        save_clans(clans)

        # Notify Leader
        if leader:
            await channel.send(f"{leader.mention}, your clan **{clan_name}** is ready! 🎉\nI have created the role {clan_role.mention} for you.")

        # Update Admin Log (Visual)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Clan Approved"
        embed.add_field(name="Approved By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"Created {channel.mention}", ephemeral=True)

        # --- LOG TO #clan-logs ---
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
        
        # DM THE LEADER
        leader = interaction.guild.get_member(leader_id)
        if leader:
            try:
                await leader.send(f"❌ Your request to create the clan **{clan_name}** was rejected by **{interaction.user.name}**.")
            except discord.Forbidden:
                pass

        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Request rejected.", ephemeral=True)

        # --- LOG TO #clan-logs ---
        await send_clan_log(interaction.guild, "🚫 Clan Rejected", 
            f"**Name:** {clan_name}\n**Applicant:** {leader.mention if leader else 'Unknown'}\n**Rejected By:** {interaction.user.mention}", 
            discord.Color.red())


# ======================================================
# 2. PERSISTENT VIEW: MEMBER APPLICATION (Leaders)
# ======================================================
class MemberApplicationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="✅ Accept", style=discord.ButtonStyle.green, custom_id="clan_app:accept")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if not clan_data:
            return await interaction.response.send_message("❌ Error: Data not found.", ephemeral=True)

        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can accept members!", ephemeral=True)

        # Get Applicant
        embed = interaction.message.embeds[0]
        applicant_id = int(embed.footer.text.split(": ")[1])
        applicant = interaction.guild.get_member(applicant_id)

        if applicant:
            # 1. Give Channel Perms
            await interaction.channel.set_permissions(applicant, read_messages=True, send_messages=True)
            
            # 2. Give Clan Role
            role_id = clan_data.get("role_id")
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    try:
                        await applicant.add_roles(role)
                    except:
                        pass # Ignore role error

            await interaction.channel.send(f"Welcome {applicant.mention} to **{clan_data['name']}**! 🎉")
            
            # Save
            if applicant.id not in clan_data["members"]:
                clan_data["members"].append(applicant.id)
                save_clans(clans)

            # --- LOG TO #clan-logs ---
            await send_clan_log(interaction.guild, "👤 Member Joined Clan", 
                f"**User:** {applicant.mention}\n**Clan:** {clan_data['name']}\n**Accepted By:** {interaction.user.mention}", 
                discord.Color.blue())

        else:
            await interaction.channel.send("User left the server, cannot add them.")

        await interaction.message.delete()

    @ui.button(label="❌ Deny", style=discord.ButtonStyle.red, custom_id="clan_app:deny")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can deny members!", ephemeral=True)

        # DM THE APPLICANT
        embed = interaction.message.embeds[0]
        applicant_id = int(embed.footer.text.split(": ")[1])
        applicant = interaction.guild.get_member(applicant_id)
        
        if applicant:
            try:
                await applicant.send(f"❌ Your application to join **{clan_data['name']}** was denied.")
            except:
                pass

        await interaction.message.delete()
        await interaction.response.send_message("Application denied.", ephemeral=True)


# ======================================================
# 3. MAIN COG
# ======================================================
class ClanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(ClanCreationView(bot))
        self.bot.add_view(MemberApplicationView())

    # --- SETUP ---
    @app_commands.command(name="setup_clan_system", description="Auto-create categories and channels for the Clan System")
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
        if not role_id: return await interaction.response.send_message("❌ Clan system not setup.", ephemeral=True)
        role = interaction.guild.get_role(role_id)
        if role not in interaction.user.roles: return await interaction.response.send_message(f"❌ You need {role.mention}.", ephemeral=True)

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
    async def apply_clan(self, interaction: discord.Interaction, clan_name: str, message: str):
        clans = load_clans()
        target_clan = None
        for cid, data in clans.items():
            if data["name"].lower() == clan_name.lower():
                target_clan = data
                break
        
        if not target_clan: return await interaction.response.send_message("❌ Clan not found.", ephemeral=True)
        if interaction.user.id in target_clan["members"]: return await interaction.response.send_message("❌ Already in this clan.", ephemeral=True)

        clan_channel = interaction.guild.get_channel(target_clan["channel_id"])
        
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
        if channel_id_str not in clans: return await interaction.response.send_message("❌ Run inside clan channel.", ephemeral=True)

        clan_data = clans[channel_id_str]
        if interaction.user.id == clan_data["leader_id"]: return await interaction.response.send_message("❌ Leaders cannot leave.", ephemeral=True)

        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        
        # Remove Role
        role_id = clan_data.get("role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role: await interaction.user.remove_roles(role)

        clan_data["members"].remove(interaction.user.id)
        save_clans(clans)
        await interaction.response.send_message(f"{interaction.user.mention} left the clan.", ephemeral=False)

        # --- LOG TO #clan-logs ---
        await send_clan_log(interaction.guild, "🚪 Member Left Clan", 
            f"**User:** {interaction.user.mention}\n**Clan:** {clan_data['name']}", 
            discord.Color.orange())

async def setup(bot):
    await bot.add_cog(ClanSystem(bot))
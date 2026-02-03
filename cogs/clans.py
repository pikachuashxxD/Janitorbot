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

# ======================================================
# 1. PERSISTENT VIEW: CLAN CREATION (Admins)
# ======================================================
class ClanCreationView(ui.View):
    def __init__(self, bot):
        # timeout=None is REQUIRED for persistence
        super().__init__(timeout=None)
        self.bot = bot

    async def get_details_from_embed(self, interaction):
        """Helper to read data from the message embed"""
        embed = interaction.message.embeds[0]
        
        # Extract Leader ID from Footer: "Leader ID: 12345"
        footer_text = embed.footer.text
        leader_id = int(footer_text.split(": ")[1])
        
        # Extract Clan Name from Field 0
        # Value format is "**ClanName**" -> strip asterisks
        clan_name = embed.fields[0].value.replace("*", "")
        
        return leader_id, clan_name

    @ui.button(label="✅ Approve", style=discord.ButtonStyle.green, custom_id="clan_req:approve")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        leader_id, clan_name = await self.get_details_from_embed(interaction)
        guild = interaction.guild
        
        # Get Config for Category
        conf = get_config(guild.id)
        cat_id = conf.get("clan_category")
        category = guild.get_channel(cat_id)

        # Get Leader Object
        leader = guild.get_member(leader_id)
        
        if not category:
            return await interaction.response.send_message("❌ Clan Category not found. Run setup again.", ephemeral=True)

        # Create Channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            leader: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True) if leader else None
        }
        
        channel_name = clan_name.lower().replace(" ", "-")
        channel = await guild.create_text_channel(name=f"🛡️・{channel_name}", category=category, overwrites=overwrites)

        # Save to DB
        clans = load_clans()
        clans[str(channel.id)] = {
            "name": clan_name,
            "leader_id": leader_id,
            "channel_id": channel.id,
            "members": [leader_id]
        }
        save_clans(clans)

        # Notify Leader inside new channel
        if leader:
            await channel.send(f"{leader.mention}, your clan **{clan_name}** is ready! 🎉\nUse this channel to manage members.")

        # Update the Request Message (Green Embed)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Clan Approved"
        embed.add_field(name="Approved By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"Created {channel.mention}", ephemeral=True)

    @ui.button(label="❌ Reject", style=discord.ButtonStyle.red, custom_id="clan_req:reject")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        # 1. Get Data (Leader ID and Clan Name) from the Embed
        leader_id, clan_name = await self.get_details_from_embed(interaction)
        
        # 2. Update the Embed (Visual Log for Admins)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Clan Rejected"
        
        # Add the "Rejected By" field
        embed.add_field(name="Rejected By", value=interaction.user.mention, inline=False)
        
        # 3. Notify the Leader (DM)
        leader = interaction.guild.get_member(leader_id)
        if leader:
            try:
                await leader.send(
                    f"❌ Your request to create the clan **{clan_name}** was rejected by **{interaction.user.name}**."
                )
            except discord.Forbidden:
                # If bot can't DM, we just ignore it (common if user has DMs off)
                pass

        # 4. Finalize
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"Rejection sent to {leader.mention if leader else 'Unknown User'}.", ephemeral=True)


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
            return await interaction.response.send_message("❌ This is not a valid clan channel.", ephemeral=True)

        # Security: Only Leader or Admin
        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can accept members!", ephemeral=True)

        # Get Applicant from Embed Footer or Description
        # We stored applicant ID in footer for persistence
        embed = interaction.message.embeds[0]
        applicant_id = int(embed.footer.text.split(": ")[1])
        applicant = interaction.guild.get_member(applicant_id)

        if applicant:
            # Grant Perms
            await interaction.channel.set_permissions(applicant, read_messages=True, send_messages=True)
            await interaction.channel.send(f"Welcome {applicant.mention} to **{clan_data['name']}**! 🎉")
            
            # Save to DB
            if applicant.id not in clan_data["members"]:
                clan_data["members"].append(applicant.id)
                save_clans(clans)
        else:
            await interaction.channel.send("User left the server, cannot add them.")

        await interaction.message.delete()

    @ui.button(label="❌ Deny", style=discord.ButtonStyle.red, custom_id="clan_app:deny")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can deny members!", ephemeral=True)

        await interaction.message.delete()
        await interaction.response.send_message("Application denied.", ephemeral=True)


# ======================================================
# 3. MAIN COG
# ======================================================
class ClanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # IMPORTANT: Register Views on startup so they work after restart!
        self.bot.add_view(ClanCreationView(bot))
        self.bot.add_view(MemberApplicationView())

    # --- SETUP COMMAND ---
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
        await interaction.followup.send(embed=embed)

    # --- CREATE CLAN ---
    @app_commands.command(name="create_clan", description="Request to create a new clan")
    async def create_clan(self, interaction: discord.Interaction, name: str, description: str):
        conf = get_config(interaction.guild_id)
        role_id = conf.get("clan_leader_role")
        
        if not role_id: return await interaction.response.send_message("❌ Clan system is not set up!", ephemeral=True)
        role = interaction.guild.get_role(role_id)
        if role not in interaction.user.roles: return await interaction.response.send_message(f"❌ You need the {role.mention} role.", ephemeral=True)

        approve_channel_id = conf.get("clan_approve_channel")
        channel = interaction.guild.get_channel(approve_channel_id)

        # REFINED EMBED
        embed = discord.Embed(title="🛡️ New Clan Request", color=0xf1c40f)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Clan Name", value=f"**{name}**", inline=True)
        embed.add_field(name="Proposed Leader", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Description", value=description, inline=False)
        # ID in footer is CRITICAL for the buttons to work
        embed.set_footer(text=f"Leader ID: {interaction.user.id}")

        # Send using the persistent view
        await channel.send(embed=embed, view=ClanCreationView(self.bot))
        await interaction.response.send_message("✅ Request Sent!", ephemeral=True)

    # --- APPLY CLAN ---
    @app_commands.command(name="apply_clan", description="Apply to join a specific clan")
    async def apply_clan(self, interaction: discord.Interaction, clan_name: str, message: str):
        clans = load_clans()
        target_clan = None
        for cid, data in clans.items():
            if data["name"].lower() == clan_name.lower():
                target_clan = data
                break
        
        if not target_clan: return await interaction.response.send_message(f"❌ Clan **{clan_name}** not found.", ephemeral=True)
        if interaction.user.id in target_clan["members"]: return await interaction.response.send_message("❌ Already in this clan!", ephemeral=True)

        clan_channel = interaction.guild.get_channel(target_clan["channel_id"])
        
        embed = discord.Embed(title="📩 New Membership Application", color=0x3498db)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Applicant", value=interaction.user.mention, inline=True)
        embed.add_field(name="Message", value=message, inline=False)
        # Applicant ID in footer for persistence
        embed.set_footer(text=f"Applicant ID: {interaction.user.id}")
        
        await clan_channel.send(content=f"<@{target_clan['leader_id']}>", embed=embed, view=MemberApplicationView())
        await interaction.response.send_message(f"✅ Application sent to **{clan_name}**!", ephemeral=True)

    # --- LEAVE CLAN ---
    @app_commands.command(name="leave_clan", description="Leave your current clan")
    async def leave_clan(self, interaction: discord.Interaction):
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)
        
        if channel_id_str not in clans:
             return await interaction.response.send_message("❌ Run this inside your clan channel.", ephemeral=True)

        clan_data = clans[channel_id_str]
        if interaction.user.id == clan_data["leader_id"]:
            return await interaction.response.send_message("❌ Leaders cannot leave! Delete the clan instead.", ephemeral=True)

        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        clan_data["members"].remove(interaction.user.id)
        save_clans(clans)
        await interaction.response.send_message(f"{interaction.user.mention} left the clan.", ephemeral=False)

async def setup(bot):
    await bot.add_cog(ClanSystem(bot))
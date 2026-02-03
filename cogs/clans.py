import discord
from discord import app_commands, ui
from discord.ext import commands
import json
import os
import asyncio
from utils.database import update_config, get_config

# --- CLAN DATABASE MANAGER (JSON) ---
CLAN_FILE = "clans.json"

def load_clans():
    if not os.path.exists(CLAN_FILE):
        return {}
    with open(CLAN_FILE, "r") as f:
        return json.load(f)

def save_clans(data):
    with open(CLAN_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- VIEWS (BUTTONS) ---

# 1. Admin Approval View (For creating a clan)
class ClanCreationView(ui.View):
    def __init__(self, bot, leader: discord.Member, clan_name: str, category_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.leader = leader
        self.clan_name = clan_name
        self.category_id = category_id

    @ui.button(label="✅ Approve", style=discord.ButtonStyle.green, custom_id="clan_approve")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        category = guild.get_channel(self.category_id)

        # Create the Clan Channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            self.leader: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True)
        }
        
        # Create text channel
        channel_name = self.clan_name.lower().replace(" ", "-")
        channel = await guild.create_text_channel(name=f"🛡️・{channel_name}", category=category, overwrites=overwrites)

        # Save to DB
        clans = load_clans()
        clans[str(channel.id)] = {
            "name": self.clan_name,
            "leader_id": self.leader.id,
            "channel_id": channel.id,
            "members": [self.leader.id]
        }
        save_clans(clans)

        # Notify Leader
        await channel.send(f"{self.leader.mention}, your clan **{self.clan_name}** has been created! 🎉\nUse this channel to manage members.")
        
        # Log it
        await interaction.message.edit(content=f"✅ **Approved** by {interaction.user.mention}", view=None, embed=None)
        await interaction.response.send_message(f"Clan created: {channel.mention}", ephemeral=True)

    @ui.button(label="❌ Reject", style=discord.ButtonStyle.red, custom_id="clan_reject")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.message.edit(content=f"❌ **Rejected** by {interaction.user.mention}", view=None, embed=None)
        # Optional: DM the leader
        try:
            await self.leader.send(f"Your request to create clan **{self.clan_name}** was rejected.")
        except:
            pass

# 2. Leader Acceptance View (For members joining)
class MemberApplicationView(ui.View):
    def __init__(self, applicant: discord.Member):
        super().__init__(timeout=None)
        self.applicant = applicant

    @ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        # Check if user is the leader (or admin)
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if not clan_data:
            return await interaction.response.send_message("❌ Error: Clan data not found.", ephemeral=True)

        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can accept members!", ephemeral=True)

        # Update Permissions
        await interaction.channel.set_permissions(self.applicant, read_messages=True, send_messages=True)
        
        # Update DB
        clan_data["members"].append(self.applicant.id)
        save_clans(clans)

        await interaction.channel.send(f"Welcome {self.applicant.mention} to **{clan_data['name']}**! 🎉")
        await interaction.message.delete() # Clean up request
        
        # Log to Server Logs
        conf = get_config(interaction.guild_id)
        log_channel_id = conf.get("clan_log_channel")
        if log_channel_id:
            log_chan = interaction.guild.get_channel(log_channel_id)
            if log_chan:
                await log_chan.send(f"👤 **Member Joined:** {self.applicant.mention} joined clan **{clan_data['name']}**")

    @ui.button(label="❌ Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        clans = load_clans()
        clan_data = clans.get(str(interaction.channel_id))
        
        if interaction.user.id != clan_data["leader_id"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the Clan Leader can deny members!", ephemeral=True)

        await interaction.message.delete()
        await interaction.response.send_message(f"Application for {self.applicant.name} denied.", ephemeral=True)


# --- MAIN COG ---
class ClanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # 1. SETUP COMMAND (Admins Only)
    # ==========================================
    @app_commands.command(name="setup_clan_system", description="Auto-create categories and channels for the Clan System")
    @app_commands.describe(leader_role="The role that gives users permission to create a clan")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_clan_system(self, interaction: discord.Interaction, leader_role: discord.Role):
        guild = interaction.guild
        await interaction.response.defer()

        # 1. Create 'Clan Admin' Category
        admin_cat = await guild.create_category("🔒 Clan Admin Logs")
        
        # 2. Create Channels inside it
        # Permissions: Only admins see these
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            leader_role: discord.PermissionOverwrite(read_messages=False) # Leaders don't see logs
        }
        
        approve_channel = await guild.create_text_channel("📜・clan-approvals", category=admin_cat, overwrites=overwrites)
        log_channel = await guild.create_text_channel("qh・clan-logs", category=admin_cat, overwrites=overwrites)

        # 3. Create 'Clans' Category (Where clans will go)
        clan_cat = await guild.create_category("🛡️ Clans")

        # 4. Save IDs to Database
        update_config(guild.id, "clan_leader_role", leader_role.id)
        update_config(guild.id, "clan_approve_channel", approve_channel.id)
        update_config(guild.id, "clan_log_channel", log_channel.id)
        update_config(guild.id, "clan_category", clan_cat.id)

        embed = discord.Embed(title="✅ Clan System Setup Complete", color=0x2ecc71)
        embed.add_field(name="Leader Role", value=leader_role.mention)
        embed.add_field(name="Approvals Channel", value=approve_channel.mention)
        embed.add_field(name="Logs Channel", value=log_channel.mention)
        embed.add_field(name="Clans Category", value=clan_cat.name)
        
        await interaction.followup.send(embed=embed)

    # ==========================================
    # 2. CREATE CLAN (Leaders Only)
    # ==========================================
    @app_commands.command(name="create_clan", description="Request to create a new clan")
    @app_commands.describe(name="Name of your clan", description="Short description of your clan")
    async def create_clan(self, interaction: discord.Interaction, name: str, description: str):
        # ... (Keep permission checks the same) ...
        conf = get_config(interaction.guild_id)
        role_id = conf.get("clan_leader_role")
        
        if not role_id:
            return await interaction.response.send_message("❌ Clan system is not set up! Ask an admin to run `/setup_clan_system`.", ephemeral=True)

        role = interaction.guild.get_role(role_id)
        if role not in interaction.user.roles:
            return await interaction.response.send_message(f"❌ You need the {role.mention} role to create a clan.", ephemeral=True)

        approve_channel_id = conf.get("clan_approve_channel")
        clan_category_id = conf.get("clan_category")
        
        if not approve_channel_id:
             return await interaction.response.send_message("❌ Approval channel not found.", ephemeral=True)

        channel = interaction.guild.get_channel(approve_channel_id)

        # --- REFINED EMBED DESIGN ---
        embed = discord.Embed(title="🛡️ New Clan Request", color=0xf1c40f)
        
        # Add Leader's avatar as a thumbnail for a polished look
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Use inline fields for a cleaner layout
        embed.add_field(name="Clan Name", value=f"**{name}**", inline=True)
        embed.add_field(name="Proposed Leader", value=interaction.user.mention, inline=True)
        
        # Description gets its own row
        embed.add_field(name="📝 Description", value=description, inline=False)
        
        # Move ID to footer for a cleaner body
        embed.set_footer(text=f"Leader ID: {interaction.user.id}")

        view = ClanCreationView(self.bot, interaction.user, name, clan_category_id)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message("✅ **Request Sent!** Admins will review your application soon.", ephemeral=True)
    # ==========================================
    # 3. APPLY TO CLAN (Anyone)
    # ==========================================
    @app_commands.command(name="apply_clan", description="Apply to join a specific clan")
    async def apply_clan(self, interaction: discord.Interaction, clan_name: str, message: str):
        # 1. Find the clan
        clans = load_clans()
        target_clan = None
        
        # Simple fuzzy search
        for channel_id, data in clans.items():
            if data["name"].lower() == clan_name.lower():
                target_clan = data
                break
        
        if not target_clan:
            return await interaction.response.send_message(f"❌ Could not find a clan named **{clan_name}**. Please check the spelling.", ephemeral=True)

        # 2. Check if already in
        if interaction.user.id in target_clan["members"]:
            return await interaction.response.send_message("❌ You are already in this clan!", ephemeral=True)

        # 3. Send Application to Clan Channel
        clan_channel = interaction.guild.get_channel(target_clan["channel_id"])
        if not clan_channel:
            return await interaction.response.send_message("❌ This clan's channel no longer exists.", ephemeral=True)

        embed = discord.Embed(title="📩 New Membership Application", color=0x3498db)
        embed.add_field(name="Applicant", value=interaction.user.mention)
        embed.add_field(name="Message", value=message)
        
        view = MemberApplicationView(interaction.user)
        
        await clan_channel.send(content=f"<@{target_clan['leader_id']}>", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Application sent to **{clan_name}**!", ephemeral=True)

    # ==========================================
    # 4. LEAVE CLAN (Members)
    # ==========================================
    @app_commands.command(name="leave_clan", description="Leave your current clan")
    async def leave_clan(self, interaction: discord.Interaction):
        # We assume the user is running this IN the clan channel, or we search
        clans = load_clans()
        channel_id_str = str(interaction.channel_id)
        
        # If run inside the clan channel
        if channel_id_str in clans:
            clan_data = clans[channel_id_str]
        else:
            # Search all clans to see if user is in one (optional logic, kept simple here)
            return await interaction.response.send_message("❌ Please run this command inside the clan channel you wish to leave.", ephemeral=True)

        if interaction.user.id == clan_data["leader_id"]:
            return await interaction.response.send_message("❌ The **Leader** cannot leave! You must delete the clan or transfer ownership.", ephemeral=True)

        if interaction.user.id not in clan_data["members"]:
             return await interaction.response.send_message("❌ You are not in this clan.", ephemeral=True)

        # Remove Perms
        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        
        # Remove from DB
        clan_data["members"].remove(interaction.user.id)
        save_clans(clans)

        await interaction.response.send_message(f"{interaction.user.mention} has left the clan.", ephemeral=False)

        # Log
        conf = get_config(interaction.guild_id)
        log_channel_id = conf.get("clan_log_channel")
        if log_channel_id:
            log_chan = interaction.guild.get_channel(log_channel_id)
            if log_chan:
                await log_chan.send(f"🚪 **Member Left:** {interaction.user.mention} left clan **{clan_data['name']}**")

async def setup(bot):
    await bot.add_cog(ClanSystem(bot))
import discord
from discord.ext import commands
from discord import app_commands
from utils.database import update_config

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="Configure the bot")

    # ====================================================
    # 1. LOGS SETUP (Added 'nickname' and 'avatar')
    # ====================================================
    @setup_group.command(name="logs", description="Set up all log channels")
    @app_commands.describe(
        join="Channel for Member Join logs",
        leave="Channel for Member Leave logs",
        voice="Channel for Voice Activity (Join/Leave/Move)",
        delete="Channel for Deleted Messages",
        edit="Channel for Edited Messages",
        mod="Channel for Mod Actions (Kick/Ban/Timeout)",
        avatar="Channel for Profile Picture Changes",     # <--- NEW
        nickname="Channel for Nickname Changes",          # <--- NEW
        roles="Channel for Role Updates (Added/Removed)"
    )
    async def logs(
        self, 
        interaction: discord.Interaction, 
        join: discord.TextChannel = None,
        leave: discord.TextChannel = None,
        voice: discord.TextChannel = None,
        delete: discord.TextChannel = None,
        edit: discord.TextChannel = None,
        mod: discord.TextChannel = None,
        avatar: discord.TextChannel = None,    # <--- NEW ARGUMENT
        nickname: discord.TextChannel = None,  # <--- NEW ARGUMENT
        roles: discord.TextChannel = None
    ):
        data = {}
        msg_parts = []

        if join:
            data["log_join_id"] = join.id
            msg_parts.append(f"✅ **Join Logs:** {join.mention}")
        if leave:
            data["log_leave_id"] = leave.id
            msg_parts.append(f"✅ **Leave Logs:** {leave.mention}")
        if voice:
            data["log_voice_id"] = voice.id
            msg_parts.append(f"✅ **Voice Logs:** {voice.mention}")
        if delete:
            data["log_delete_id"] = delete.id
            msg_parts.append(f"✅ **Delete Logs:** {delete.mention}")
        if edit:
            data["log_edit_id"] = edit.id
            msg_parts.append(f"✅ **Edit Logs:** {edit.mention}")
        if mod:
            data["log_mod_id"] = mod.id
            msg_parts.append(f"✅ **Mod Logs:** {mod.mention}")
        
        # --- NEW SEPARATE OPTIONS ---
        if avatar:
            data["log_avatar_id"] = avatar.id
            msg_parts.append(f"✅ **Avatar Logs:** {avatar.mention}")
        if nickname:
            data["log_nickname_id"] = nickname.id
            msg_parts.append(f"✅ **Nickname Logs:** {nickname.mention}")
        if roles:
            data["log_role_id"] = roles.id
            msg_parts.append(f"✅ **Role Logs:** {roles.mention}")

        if data:
            for key, value in data.items():
                update_config(interaction.guild_id, key, value)
            await interaction.response.send_message("\n".join(msg_parts))
        else:
            await interaction.response.send_message("❌ You didn't select any channels to setup!", ephemeral=True)

    # ====================================================
    # 2. CLAN SETUP
    # ====================================================
    @setup_group.command(name="clans", description="Configure the Clan System")
    @app_commands.describe(role="The role required to create clans (e.g. @VIP)")
    async def clans(self, interaction: discord.Interaction, role: discord.Role):
        update_config(interaction.guild_id, "clan_role_id", role.id)
        await interaction.response.send_message(f"✅ **Clan System Configured!**\nUsers need the {role.mention} role to create clans.")

    # ====================================================
    # 3. WELCOME SETUP
    # ====================================================
    @setup_group.command(name="welcome", description="Set channel for Welcome Cards")
    async def welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "welcome_channel_id", channel.id)
        await interaction.response.send_message(f"✅ **Welcome Cards** set to {channel.mention}")

    # ====================================================
    # 4. STREAMER SETUP
    # ====================================================
    @setup_group.command(name="stream", description="Configure Streamer Alerts")
    @app_commands.describe(
        role="The Role required to trigger alerts (e.g. @Streamer)",
        channel_normal="Channel where normal alerts go",
        channel_owner="Channel where Owner/VIP alerts go"
    )
    async def stream(
        self, 
        interaction: discord.Interaction, 
        role: discord.Role = None, 
        channel_normal: discord.TextChannel = None, 
        channel_owner: discord.TextChannel = None
    ):
        data = {}
        msg_parts = []

        if role:
            data["streamer_role_id"] = role.id
            msg_parts.append(f"✅ **Streamer Role:** {role.mention}")
        if channel_normal:
            data["stream_channel_normal"] = channel_normal.id
            msg_parts.append(f"✅ **Normal Alerts:** {channel_normal.mention}")
        if channel_owner:
            data["stream_channel_owner"] = channel_owner.id
            msg_parts.append(f"✅ **Owner Alerts:** {channel_owner.mention}")

        if data:
            for key, value in data.items():
                update_config(interaction.guild_id, key, value)
            await interaction.response.send_message("\n".join(msg_parts))
        else:
            await interaction.response.send_message("❌ You didn't select any options to update!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
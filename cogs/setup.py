import discord
from discord import app_commands
from discord.ext import commands
from utils.database import update_config
import config

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="Configure the bot")

    # ====================================================
    # 1. LOGS SETUP (Merged Command)
    # ====================================================
    @setup_group.command(name="logs", description="Set up all log channels in one command")
    @app_commands.describe(
        join="Channel for Member Join logs",
        leave="Channel for Member Leave logs",
        voice="Channel for Voice Activity (Join/Leave/Move)",
        delete="Channel for Deleted Messages",
        edit="Channel for Edited Messages",
        mod="Channel for Mod Actions (Kick/Ban/Timeout)"
    )
    async def logs(
        self, 
        interaction: discord.Interaction, 
        join: discord.TextChannel = None,
        leave: discord.TextChannel = None,
        voice: discord.TextChannel = None,
        delete: discord.TextChannel = None,
        edit: discord.TextChannel = None,
        mod: discord.TextChannel = None
    ):
        """
        Set multiple log channels at once. You only need to select the ones you want to change.
        """
        changes = []

        if join:
            update_config(interaction.guild_id, "log_join_id", join.id)
            changes.append(f"✅ **Join Logs:** {join.mention}")
        
        if leave:
            update_config(interaction.guild_id, "log_leave_id", leave.id)
            changes.append(f"✅ **Leave Logs:** {leave.mention}")

        if voice:
            update_config(interaction.guild_id, "log_voice_id", voice.id)
            changes.append(f"✅ **Voice Logs:** {voice.mention}")

        if delete:
            update_config(interaction.guild_id, "log_delete_id", delete.id)
            changes.append(f"✅ **Delete Logs:** {delete.mention}")

        if edit:
            update_config(interaction.guild_id, "log_edit_id", edit.id)
            changes.append(f"✅ **Edit Logs:** {edit.mention}")

        if mod:
            update_config(interaction.guild_id, "log_mod_id", mod.id)
            changes.append(f"✅ **Mod Logs:** {mod.mention}")

        if changes:
            await interaction.response.send_message("\n".join(changes))
        else:
            await interaction.response.send_message("❌ You didn't select any channels to setup!", ephemeral=True)

    # ====================================================
    # 2. WELCOME SETUP (Simple Channel Selection)
    # ====================================================
    @setup_group.command(name="welcome", description="Set channel for Welcome Cards")
    async def welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "welcome_channel_id", channel.id)
        await interaction.response.send_message(f"✅ **Welcome Cards** set to {channel.mention}")

    # ====================================================
    # 3. STREAMER SETUP (Merged Command)
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
        """
        Configure all streamer settings in one command.
        """
        changes = []

        if role:
            update_config(interaction.guild_id, "streamer_role_id", role.id)
            changes.append(f"✅ **Streamer Role:** {role.mention}")

        if channel_normal:
            update_config(interaction.guild_id, "stream_channel_normal", channel_normal.id)
            changes.append(f"✅ **Normal Alerts:** {channel_normal.mention}")

        if channel_owner:
            update_config(interaction.guild_id, "stream_channel_owner", channel_owner.id)
            changes.append(f"✅ **Owner Alerts:** {channel_owner.mention}")

        if changes:
            await interaction.response.send_message("\n".join(changes))
        else:
            await interaction.response.send_message("❌ You didn't select any options to update!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
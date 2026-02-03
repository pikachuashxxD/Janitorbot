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
    # 2. WELCOME SETUP (Merged & Conditional)
    # ====================================================
    @setup_group.command(name="welcome", description="Setup Welcome Channel & Optional Message")
    @app_commands.describe(
        channel="Where to send the welcome card",
        message="Custom 'Get Started' text (Leave empty to hide that section)"
    )
    async def welcome(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str = None):
        # 1. Save the Channel
        update_config(interaction.guild_id, "welcome_channel_id", channel.id)
        
        response = f"✅ **Welcome Channel** set to {channel.mention}"

        # 2. Handle the Message
        if message:
            # User provided text -> Save it
            update_config(interaction.guild_id, "welcome_custom_text", message)
            response += f"\n📝 **Custom Message set:**\n> {message}"
        else:
            # User left it empty -> Set to None (Hide the section)
            update_config(interaction.guild_id, "welcome_custom_text", None)
            response += "\n🗑️ **Custom Message cleared.** (The 'Get Started' section will be hidden)"

        await interaction.response.send_message(response)

    # ====================================================
    # 3. STREAMER SETUP (Keeping as is)
    # ====================================================
    @setup_group.command(name="streamer_role", description="Set the Role required to trigger stream alerts")
    async def streamer_role(self, interaction: discord.Interaction, role: discord.Role):
        update_config(interaction.guild_id, "streamer_role_id", role.id)
        await interaction.response.send_message(f"✅ **Streamer Role** set to {role.mention}")

    @setup_group.command(name="stream_channel_normal", description="Channel for normal streamers")
    async def stream_channel_normal(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "stream_channel_normal", channel.id)
        await interaction.response.send_message(f"✅ **Normal Alerts** set to {channel.mention}")

    @setup_group.command(name="stream_channel_owner", description="Channel for Owner/VIP streamers")
    async def stream_channel_owner(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "stream_channel_owner", channel.id)
        await interaction.response.send_message(f"✅ **Owner Alerts** set to {channel.mention}")

async def setup(bot):
    await bot.add_cog(Setup(bot))
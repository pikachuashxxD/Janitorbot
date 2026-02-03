import discord
from discord import app_commands
from discord.ext import commands
from utils.database import update_config
import config

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="Configure the bot")

    # --- 1. JOIN LOGS ---
    @setup_group.command(name="logs_join", description="Set channel for Member Join logs")
    async def logs_join(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_join_id", channel.id)
        await interaction.response.send_message(f"✅ **Join Logs** will be sent to {channel.mention}")

    # --- 2. LEAVE LOGS ---
    @setup_group.command(name="logs_leave", description="Set channel for Member Leave logs")
    async def logs_leave(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_leave_id", channel.id)
        await interaction.response.send_message(f"✅ **Leave Logs** will be sent to {channel.mention}")

    # --- 3. VC LOGS ---
    @setup_group.command(name="logs_voice", description="Set channel for Voice Activity logs")
    async def logs_voice(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_voice_id", channel.id)
        await interaction.response.send_message(f"✅ **Voice Logs** will be sent to {channel.mention}")

    # --- 4. DELETE LOGS (New!) ---
    @setup_group.command(name="logs_delete", description="Set channel for Deleted Messages")
    async def logs_delete(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_delete_id", channel.id)
        await interaction.response.send_message(f"✅ **Delete Logs** will be sent to {channel.mention}")

    # --- 5. EDIT LOGS (New!) ---
    @setup_group.command(name="logs_edit", description="Set channel for Edited Messages")
    async def logs_edit(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_edit_id", channel.id)
        await interaction.response.send_message(f"✅ **Edit Logs** will be sent to {channel.mention}")

    # --- 6. MOD LOGS ---
    @setup_group.command(name="logs_mod", description="Set channel for Kicks, Bans, and Timeouts")
    async def logs_mod(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_mod_id", channel.id)
        await interaction.response.send_message(f"✅ **Mod Logs** will be sent to {channel.mention}")

    # --- STREAMER CONFIG ---
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

    # --- UPDATED WELCOME COMMANDS ---
    
    @setup_group.command(name="welcome_channel", description="Set channel for Welcome Cards")
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "welcome_channel_id", channel.id)
        await interaction.response.send_message(f"✅ **Welcome Cards** set to {channel.mention}")

    @setup_group.command(name="welcome_message", description="Set custom text for the 'Get Started' field")
    async def welcome_message(self, interaction: discord.Interaction, message: str):
        """
        Example usage: 
        /setup welcome_message message:"Read the rules in #rules and pick roles in #roles!"
        """
        # Save the custom string to the database
        update_config(interaction.guild_id, "welcome_custom_text", message)
        await interaction.response.send_message(f"✅ **Get Started Text** updated:\n> {message}")

    # ... (Keep the rest of your Streamer commands here) ...

async def setup(bot):
    await bot.add_cog(Setup(bot))
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import update_config
import config

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="Configure the bot for your server")

    @setup_group.command(name="logs", description="Set the channel for audit logs")
    @app_commands.describe(channel="The channel where logs will be sent")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "log_channel_id", channel.id)
        
        embed = discord.Embed(
            description=f"✅ **Audit Logs** will now be sent to {channel.mention}",
            color=config.COLOR_GREEN
        )
        await interaction.response.send_message(embed=embed)

    @setup_group.command(name="welcome", description="Set the channel for welcome messages")
    @app_commands.describe(channel="The channel where welcome cards will appear")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "welcome_channel_id", channel.id)
        
        embed = discord.Embed(
            description=f"✅ **Welcome Messages** will now be sent to {channel.mention}",
            color=config.COLOR_GREEN
        )
        await interaction.response.send_message(embed=embed)

    @setup_group.command(name="stream", description="Set the channel for stream alerts")
    @app_commands.describe(channel="The channel where live notifications will appear")
    @app_commands.checks.has_permissions(administrator=True)
    async def stream(self, interaction: discord.Interaction, channel: discord.TextChannel):
        update_config(interaction.guild_id, "stream_channel_id", channel.id)
        
        embed = discord.Embed(
            description=f"✅ **Stream Alerts** will now be sent to {channel.mention}",
            color=config.COLOR_GREEN
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Setup(bot))
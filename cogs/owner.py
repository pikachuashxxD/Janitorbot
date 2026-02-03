import discord
from discord import app_commands
from discord.ext import commands
import datetime
import traceback
import config

class BotStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # This hooks the "Slash Command" error handler to our function below
        self.bot.tree.on_error = self.on_app_command_error

    # --- HELPER: Get the Log Channel ---
    def get_log_channel(self):
        if hasattr(config, 'BOT_LOG_CHANNEL'):
            return self.bot.get_channel(config.BOT_LOG_CHANNEL)
        return None

    # ====================================================
    # 1. ERROR LOGGING (Global)
    # ====================================================
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # 1. Tell the user something went wrong (so they aren't waiting)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred while processing this command.", ephemeral=True)

        # 2. Get the Log Channel
        channel = self.get_log_channel()
        if not channel: 
            print(f"Error: {error}") # Fallback to console if no channel set
            return

        # 3. Build the Error Report
        embed = discord.Embed(title="⚠️ Bot Error Occurred", color=discord.Color.red(), timestamp=datetime.datetime.now())
        
        # Who caused it?
        embed.add_field(name="User", value=f"{interaction.user.name} (`{interaction.user.id}`)", inline=True)
        
        # Where did it happen?
        if interaction.guild:
            embed.add_field(name="Guild", value=f"{interaction.guild.name} (`{interaction.guild.id}`)", inline=True)
        else:
            embed.add_field(name="Guild", value="Direct Messages", inline=True)

        # What command?
        embed.add_field(name="Command", value=f"/{interaction.command.name}" if interaction.command else "Unknown", inline=True)

        # The Error Traceback (limit to 1000 chars to fit in embed)
        error_msg = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        embed.description = f"```py\n{error_msg[:4000]}```"

        await channel.send(embed=embed)

    # ====================================================
    # 2. BOT JOINED A SERVER
    # ====================================================
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = self.get_log_channel()
        if not channel: return

        embed = discord.Embed(title="📈 Bot Joined New Server", color=discord.Color.green(), timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="Server Name", value=f"**{guild.name}**", inline=True)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner", value=f"{guild.owner.name} (`{guild.owner_id}`)", inline=False)
        embed.add_field(name="Member Count", value=f"{guild.member_count} Members", inline=True)
        embed.add_field(name="Created At", value=discord.utils.format_dt(guild.created_at, "R"), inline=True)

        await channel.send(embed=embed)

    # ====================================================
    # 3. BOT KICKED / LEFT A SERVER
    # ====================================================
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self.get_log_channel()
        if not channel: return

        embed = discord.Embed(title="📉 Bot Left Server", color=discord.Color.red(), timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="Server Name", value=f"**{guild.name}**", inline=True)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Member Count", value=f"{guild.member_count} Members", inline=False)

        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotStats(bot))
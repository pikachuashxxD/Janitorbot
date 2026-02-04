import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import time
from utils.database import get_config, update_config

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Set the start time when the Cog loads
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        # Start the background task to update the live message
        self.update_status_task.start()

    def cog_unload(self):
        self.update_status_task.cancel()

    def get_uptime(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - self.start_time
        
        days = delta.days
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        return f"{days}d {hours}h {minutes}m {secs}s"

    def create_status_embed(self):
        # Calculate Stats
        server_count = len(self.bot.guilds)
        # Sum member count from all servers
        member_count = sum(g.member_count for g in self.bot.guilds)
        uptime = self.get_uptime()
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🤖 Bot System Status",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="⏱️ Uptime", value=f"```yaml\n{uptime}\n```", inline=False)
        
        embed.add_field(name="🛡️ Servers", value=f"**{server_count}** Guilds", inline=True)
        embed.add_field(name="👥 Members", value=f"**{member_count}** Users", inline=True)
        embed.add_field(name="📶 Ping", value=f"**{latency}ms**", inline=True)
        
        embed.set_footer(text="Updates every 2 minutes", icon_url=self.bot.user.display_avatar.url)
        return embed

    # ====================================================
    # 1. SIMPLE STATUS COMMAND (View Once)
    # ====================================================
    @app_commands.command(name="status", description="Show the bot's current uptime and stats")
    async def status(self, interaction: discord.Interaction):
        embed = self.create_status_embed()
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # 2. SETUP COMMAND (Create Live Dashboard)
    # ====================================================
    @app_commands.command(name="setup_status", description="Create a live updating status message in this channel")
    @app_commands.describe(channel="The channel where the status message should stay")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_status(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()
        
        # 1. Send the initial message
        embed = self.create_status_embed()
        msg = await channel.send(embed=embed)

        # 2. Save the Channel ID and Message ID to database
        update_config(interaction.guild_id, "status_channel_id", channel.id)
        update_config(interaction.guild_id, "status_message_id", msg.id)

        await interaction.followup.send(f"✅ **Live Status** created in {channel.mention}! It will update every 2 minutes.")

    # ====================================================
    # 3. BACKGROUND TASK (Updates the Message)
    # ====================================================
    @tasks.loop(minutes=2)
    async def update_status_task(self):
        await self.bot.wait_until_ready()
        
        # Iterate through all guilds the bot is in
        for guild in self.bot.guilds:
            try:
                data = get_config(guild.id)
                channel_id = data.get("status_channel_id")
                message_id = data.get("status_message_id")

                if channel_id and message_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        try:
                            message = await channel.fetch_message(message_id)
                            # Update the embed
                            new_embed = self.create_status_embed()
                            await message.edit(embed=new_embed)
                        except discord.NotFound:
                            # Message was deleted, remove config to stop errors
                            update_config(guild.id, "status_message_id", None)
                        except discord.Forbidden:
                            pass # Bot lost permissions
            except Exception as e:
                print(f"[Status Task Error] Guild {guild.id}: {e}")

async def setup(bot):
    await bot.add_cog(BotStatus(bot))
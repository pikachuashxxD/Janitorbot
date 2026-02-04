import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import asyncio
import config
from utils.database import get_config, update_config

# ====================================================
# 🎨 CONFIGURATION: PASTE YOUR LINKS HERE
# ====================================================
# 1. Top Right Small Logo (Thumbnail)
# Set to None to use the Bot's Avatar automatically.
THUMBNAIL_URL = "https://media.discordapp.net/attachments/973160783196323860/1468515977112195259/Skirichu_gif.gif?ex=69844d94&is=6982fc14&hm=798a17ad820646668a8e186925fadf2c2ac520d65bf61dadc9acba758e902d2c&=&width=320&height=320" 
# Example: "https://i.imgur.com/SmallLogo.png"

# 2. Bottom Large Banner (Image)
# Set to None if you don't want a banner.
BANNER_URL = "None" 
# Example: "https://i.imgur.com/BigBanner.png"


class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.update_status_task.start()
        self._has_logged_startup = False

    def cog_unload(self):
        self.update_status_task.cancel()
        asyncio.create_task(self.send_shutdown_log())

    def get_uptime(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - self.start_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        secs = delta.seconds % 60
        time_str = f"{hours:02}:{minutes:02}:{secs:02}"
        if days > 0:
            return f"{days}d {time_str}"
        return time_str

    def get_bot_log_channel(self):
        if hasattr(config, 'BOT_LOG_CHANNEL'):
            return self.bot.get_channel(config.BOT_LOG_CHANNEL)
        return None

    # ====================================================
    # 1. LIVE STATUS EMBED
    # ====================================================
    def create_status_embed(self):
        server_count = len(self.bot.guilds)
        member_count = sum(g.member_count for g in self.bot.guilds)
        uptime = self.get_uptime()
        latency = round(self.bot.latency * 1000)
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        embed = discord.Embed(
            title=self.bot.user.name,
            color=discord.Color.green()
        )
        
        # --- 1. SET THUMBNAIL (Top Right) ---
        if THUMBNAIL_URL:
            embed.set_thumbnail(url=THUMBNAIL_URL)
        else:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # --- 2. SET BANNER (Bottom Large) ---
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)

        # --- DATA FIELDS ---
        # Row 1: STATUS | SERVERS | PING
        embed.add_field(name="🟢 STATUS", value="```\nOnline\n```", inline=True)
        embed.add_field(name="🛡️ SERVERS", value=f"```\n{server_count}\n```", inline=True)
        embed.add_field(name="📶 PING", value=f"```\n{latency}ms\n```", inline=True)

        # Row 2: MEMBERS
        embed.add_field(name="👥 MEMBERS", value=f"```\n{member_count}\n```", inline=True)
        
        # Row 3: UPTIME
        embed.add_field(name="⏳ UPTIME", value=f"```\n{uptime}\n```", inline=False)
        
        embed.set_footer(text=f"Last Updated: {current_time}")
        
        return embed

    # ====================================================
    # 2. EVENTS
    # ====================================================
    @commands.Cog.listener()
    async def on_ready(self):
        if self._has_logged_startup: return
        self._has_logged_startup = True

        channel = self.get_bot_log_channel()
        if channel:
            embed = discord.Embed(
                title="🟢 Bot is Online!",
                description=f"**{self.bot.user.name}** is now up and running.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Ping", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
            embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
            embed.set_footer(text="System Startup")
            await channel.send(embed=embed)

    async def send_shutdown_log(self):
        channel = self.get_bot_log_channel()
        if channel:
            uptime = self.get_uptime()
            embed = discord.Embed(
                title="🔴 Bot is Shutting Down",
                description="System shutdown initiated.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Session Uptime", value=f"`{uptime}`", inline=False)
            embed.set_footer(text="System Shutdown")
            await channel.send(embed=embed)

    # ====================================================
    # 3. COMMANDS
    # ====================================================
    @app_commands.command(name="setup_status", description="Create a live updating status message")
    @app_commands.describe(channel="The channel for the live dashboard")
    async def setup_status(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message("❌ **Access Denied:** Only the Bot Owner can run this command.", ephemeral=True)
            return

        await interaction.response.defer()
        
        embed = self.create_status_embed()
        msg = await channel.send(embed=embed)

        update_config(interaction.guild_id, "status_channel_id", channel.id)
        update_config(interaction.guild_id, "status_message_id", msg.id)

        await interaction.followup.send(f"✅ **Live Status** created in {channel.mention}!")

    @app_commands.command(name="status", description="Show uptime and stats")
    async def status(self, interaction: discord.Interaction):
        embed = self.create_status_embed()
        await interaction.response.send_message(embed=embed)

    @tasks.loop(minutes=2)
    async def update_status_task(self):
        await self.bot.wait_until_ready()
        
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
                            await message.edit(embed=self.create_status_embed())
                        except (discord.NotFound, discord.Forbidden):
                            update_config(guild.id, "status_message_id", None)
            except Exception as e:
                print(f"[Status Task] Error in {guild.name}: {e}")

async def setup(bot):
    await bot.add_cog(BotStatus(bot))
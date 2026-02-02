import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class Streamer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stream_cooldowns = {} # {user_id: datetime}

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if not after.guild: return

        # 1. Get Stream Channel from DB
        data = get_config(after.guild.id)
        channel_id = data.get("stream_channel_id")
        if not channel_id: return
        
        channel = self.bot.get_channel(channel_id)
        if not channel: return

        # 2. Detect Streaming
        is_streaming = any(isinstance(a, discord.Streaming) for a in after.activities)
        was_streaming = any(isinstance(a, discord.Streaming) for a in before.activities)

        if is_streaming and not was_streaming:
            # 3. Cooldown Logic (The Fix)
            user_id = after.id
            now = datetime.datetime.now()
            
            if user_id in self.stream_cooldowns:
                last_alert_time = self.stream_cooldowns[user_id]
                # Check if less than 12 hours (43200 seconds)
                if (now - last_alert_time).total_seconds() < 43200:
                    return # Stop, don't spam

            # 4. Get Activity Details
            activity = next(a for a in after.activities if isinstance(a, discord.Streaming))
            
            # 5. Send Alert
            embed = discord.Embed(
                title=f"🔴 {after.display_name} is LIVE!",
                description=f"**{activity.name}**\n\n[Click here to Watch!]({activity.url})",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_image(url=activity.assets.get('large_image_url') if hasattr(activity, 'assets') else None)
            
            await channel.send(content=f"Hey @everyone! **{after.name}** is live!", embed=embed)
            
            # 6. Update Cooldown
            self.stream_cooldowns[user_id] = now

async def setup(bot):
    await bot.add_cog(Streamer(bot))
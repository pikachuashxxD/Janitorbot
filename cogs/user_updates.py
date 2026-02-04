import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class UserUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        # Using the main log channel for these updates
        # You can change "log_channel" to "log_edit_id" if you want them with message edits
        data = get_config(guild.id)
        channel_id = data.get("log_channel") 
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = self.get_log_channel(before.guild)
        if not channel: return

        now = discord.utils.utcnow()

        # ====================================================
        # 1. NICKNAME CHANGES
        # ====================================================
        if before.nick != after.nick:
            embed = discord.Embed(
                title="🏷️ Nickname Changed",
                color=discord.Color.blue(),
                timestamp=now
            )
            embed.set_author(name=after.name, icon_url=after.display_avatar.url)
            
            # Helper to show "None" if they reset their nickname
            before_nick = before.nick if before.nick else "[None] (Username)"
            after_nick = after.nick if after.nick else "[None] (Username)"

            embed.add_field(name="Before", value=f"`{before_nick}`", inline=True)
            embed.add_field(name="After", value=f"`{after_nick}`", inline=True)
            
            embed.set_footer(text=f"ID: {after.id}")
            await channel.send(embed=embed)

        # ====================================================
        # 2. PROFILE PICTURE CHANGES
        # ====================================================
        # Check if the display avatar changed (covers both Server Profile and Global Profile)
        if before.display_avatar.url != after.display_avatar.url:
            embed = discord.Embed(
                title="🖼️ Avatar Changed",
                description=f"{after.mention} updated their profile picture.",
                color=discord.Color.gold(),
                timestamp=now
            )
            embed.set_author(name=after.name, icon_url=after.display_avatar.url)
            
            # Show the OLD avatar as a thumbnail (small, top right)
            embed.set_thumbnail(url=before.display_avatar.url)
            
            # Show the NEW avatar as the main image (big)
            embed.set_image(url=after.display_avatar.url)
            
            embed.set_footer(text=f"ID: {after.id}")
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserUpdates(bot))
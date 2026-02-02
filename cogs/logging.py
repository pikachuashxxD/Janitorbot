import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {} # Tracks time spent in VC

    # --- HELPER: Get Log Channel ---
    def get_log_channel(self, guild):
        data = get_config(guild.id)
        channel_id = data.get("log_channel_id")
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    # --- MESSAGE DELETE LOG ---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        
        channel = self.get_log_channel(message.guild)
        if channel:
            # Create the "Beautified" Embed
            embed = discord.Embed(
                description=f"**Message sent by {message.author.mention} deleted in {message.channel.mention}**",
                color=config.COLOR_RED,
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name="Message Deleted", icon_url=message.author.display_avatar.url)
            
            # Content handling (Code block for clean look)
            content = message.content if message.content else "*[Image/Embed Only]*"
            embed.add_field(name=f"{config.EMOJIS['trash']} Deleted Content", value=f"```\n{content}\n```", inline=False)
            
            embed.set_footer(text=f"User ID: {message.author.id}")
            await channel.send(embed=embed)

    # --- MESSAGE EDIT LOG ---
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        
        channel = self.get_log_channel(before.guild)
        if channel:
            embed = discord.Embed(
                description=f"**Message edited in {before.channel.mention}** [Jump to Message]({after.jump_url})",
                color=config.COLOR_BLUE,
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name=f"{before.author.name} Edited a Message", icon_url=before.author.display_avatar.url)
            
            # Spacing with Emoji Headers
            embed.add_field(name=f"{config.EMOJIS['edit']} Before", value=f"{before.content}", inline=False)
            embed.add_field(name="\u200b", value="\u200b", inline=False) # Spacer
            embed.add_field(name=f"{config.EMOJIS['sparkles']} After", value=f"{after.content}", inline=False)
            
            embed.set_footer(text=f"User ID: {before.author.id}")
            await channel.send(embed=embed)

    # --- VOICE LOGS ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = self.get_log_channel(member.guild)
        if not channel: return

        # JOIN
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = datetime.datetime.now()
            embed = discord.Embed(description=f"**{member.mention} joined voice channel**", color=config.COLOR_GREEN)
            embed.add_field(name="Channel", value=f"{config.EMOJIS['voice_join']} {after.channel.name}")
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

        # LEAVE
        elif before.channel is not None and after.channel is None:
            # Calculate Duration
            duration_str = "Unknown"
            if member.id in self.voice_sessions:
                start_time = self.voice_sessions.pop(member.id)
                duration = datetime.datetime.now() - start_time
                minutes = int(duration.total_seconds() // 60)
                hours = minutes // 60
                duration_str = f"{hours}h {minutes % 60}m" if hours > 0 else f"{minutes}m"

            embed = discord.Embed(description=f"**{member.mention} left voice channel**", color=config.COLOR_RED)
            embed.add_field(name="Channel", value=f"{config.EMOJIS['voice_leave']} {before.channel.name}", inline=True)
            embed.add_field(name="Session Duration", value=f"⏱️ {duration_str}", inline=True)
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

        # MOVED
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(description=f"**{member.mention} moved voice channels**", color=config.COLOR_GOLD)
            embed.add_field(name="From", value=f"{config.EMOJIS['voice_leave']} {before.channel.name}", inline=True)
            embed.add_field(name="To", value=f"{config.EMOJIS['voice_join']} {after.channel.name}", inline=True)
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
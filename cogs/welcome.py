import discord
from discord.ext import commands
import config
from utils.database import get_config

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Helper: Find channel by name ---
    def get_channel_mention(self, guild, possible_names):
        """Returns channel mention if found, otherwise returns None."""
        for name in possible_names:
            channel = discord.utils.get(guild.channels, name=name)
            if channel:
                return channel.mention
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = get_config(member.guild.id)
        channel_id = data.get("welcome_channel_id")
        
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)

        if channel:
            # 1. Build "Get Started" Lines
            get_started_lines = []
            
            rules_channel = self.get_channel_mention(member.guild, ["rules", "info", "server-rules"])
            if rules_channel:
                get_started_lines.append(f"📜 **Rules:** {rules_channel}")
                
            news_channel = self.get_channel_mention(member.guild, ["updates", "news", "announcements"])
            if news_channel:
                get_started_lines.append(f"📢 **News:** {news_channel}")

            # 2. Build "Gaming Zones" Lines
            gaming_lines = []
            
            mc_channel = self.get_channel_mention(member.guild, ["minecraft", "mc-server", "minecraft-info"])
            if mc_channel:
                gaming_lines.append(f"⛏️ **Minecraft:** {mc_channel}")
                
            steam_channel = self.get_channel_mention(member.guild, ["steam-ids", "steam", "codes"])
            if steam_channel:
                gaming_lines.append(f"🚂 **Steam Codes:** {steam_channel}")

            # 3. Create Embed
            description = (
                f"We're absolutely **thrilled** to have you join the **{member.guild.name} gaming community!** 🎉\n\n"
                "We are dedicated to providing a fun, high-performance gaming experience for everyone.\n\n"
                "*Dive in, explore, and **most importantly** have fun!*"
            )

            embed = discord.Embed(description=description, color=0x2b2d31)
            embed.set_author(name=f"Welcome to {member.guild.name}, {member.name}!", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)

            # 4. Add Fields ONLY if they have content
            if get_started_lines:
                embed.add_field(name="🚀 Get Started", value="\n".join(get_started_lines), inline=False)
            
            if gaming_lines:
                embed.add_field(name="🎮 Gaming Zones", value="\n".join(gaming_lines), inline=False)
            
            # Support Us (Always Show)
            embed.add_field(
                name="📺 Support Us", 
                value="[Subscribe to our YouTube Channel!](https://youtube.com)", 
                inline=False
            )

            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
            await channel.send(content=f"Welcome {member.mention}! 👋", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
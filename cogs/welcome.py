import discord
from discord.ext import commands
import config
from utils.database import get_config

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_channel_mention(self, guild, possible_names):
        for name in possible_names:
            channel = discord.utils.get(guild.channels, name=name)
            if channel:
                return channel.mention
        return f"#{possible_names[0]}"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = get_config(member.guild.id)
        channel_id = data.get("welcome_channel_id")
        
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)

        if channel:
            # 1. Build Description
            description = (
                f"We're absolutely **thrilled** to have you join the **{member.guild.name} gaming community!** 🎉\n\n"
                "We are dedicated to providing a fun, high-performance gaming experience for everyone.\n\n"
                "*Dive in, explore, and **most importantly** have fun!*"
            )

            embed = discord.Embed(description=description, color=0x2b2d31)
            embed.set_author(name=f"Welcome to {member.guild.name}, {member.name}!", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)

            # 2. CONDITIONAL "Get Started" Field
            # Only show if user set a custom message
            custom_msg = data.get("welcome_custom_text")
            if custom_msg:
                embed.add_field(name="🚀 Get Started", value=custom_msg, inline=False)
            
            # 3. Gaming Zones (Always show - Smart Links)
            mc_link = self.get_channel_mention(member.guild, ["minecraft", "mc-server", "minecraft-info"])
            steam_link = self.get_channel_mention(member.guild, ["steam-ids", "steam", "codes"])
            
            embed.add_field(
                name="🎮 Gaming Zones", 
                value=f"⛏️ **Minecraft:** {mc_link}\n🚂 **Steam Codes:** {steam_link}", 
                inline=False
            )
            
            # 4. Support Us (Always show)
            embed.add_field(
                name="📺 Support Us", 
                value="[Subscribe to our YouTube Channel!](https://youtube.com)", 
                inline=False
            )

            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
            await channel.send(content=f"Welcome {member.mention}! 👋", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
import discord
from discord.ext import commands
import config
from utils.database import get_config

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # 1. Get the Welcome Channel from DB
        data = get_config(member.guild.id)
        channel_id = data.get("welcome_channel_id")
        
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if channel:
            # 2. Build the "SkiriChu" Style Embed
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}, {member.name}! {config.EMOJIS['welcome']}",
                description=(
                    f"We're absolutely **thrilled** to have you join our community! {config.EMOJIS['sparkles']}\n\n"
                    "We are dedicated to providing a fun, high-performance gaming experience for everyone.\n\n"
                    "*Dive in, explore, and **most importantly** have fun!*"
                ),
                color=0x2b2d31 # The Dark Grey theme you liked
            )
            
            # Fields with Spacing
            embed.add_field(name="🚀 Get Started", value="Check out the server rules and say hi!", inline=False)
            
            # Dynamic Member Count
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
            
            # 3. Send Message
            try:
                await channel.send(content=f"Welcome {member.mention}!", embed=embed)
            except discord.Forbidden:
                print(f"❌ Could not send welcome message in {member.guild.name}")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
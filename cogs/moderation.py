import discord
from discord import app_commands
from discord.ext import commands
import datetime
import config
from collections import defaultdict

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Anti-Spam Tracking: {user_id: [timestamp, timestamp, ...]}
        self.spam_check = defaultdict(list)

    # --- HELPER: DM User ---
    async def dm_user(self, member, action, reason, moderator):
        try:
            embed = discord.Embed(title=f"🛑 You were {action}", color=config.COLOR_RED)
            embed.add_field(name="Server", value=member.guild.name, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Actioned by {moderator}")
            await member.send(embed=embed)
        except discord.Forbidden:
            pass # DM closed

    # --- AUTOMOD LISTENER ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        
        # 1. LINK FILTER
        if "http" in message.content.lower():
            # Whitelist
            allowed = ["youtube.com", "youtu.be", "twitch.tv", "discord.com"]
            if not any(domain in message.content.lower() for domain in allowed):
                # Check permissions (Admins bypass)
                if not message.author.guild_permissions.administrator:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, unauthorized links are not allowed!", delete_after=5)
                    return

        # 2. ANTI-SPAM (5 messages in 5 seconds)
        now = datetime.datetime.now().timestamp()
        self.spam_check[message.author.id].append(now)
        
        # Remove timestamps older than 5 seconds
        self.spam_check[message.author.id] = [t for t in self.spam_check[message.author.id] if now - t < 5]
        
        if len(self.spam_check[message.author.id]) >= 5:
            # TRIGGER SPAM PROTECTION
            if not message.author.guild_permissions.administrator:
                try:
                    # Timeout for 10 minutes
                    duration = datetime.timedelta(minutes=10)
                    await message.author.timeout(duration, reason="Anti-Spam Auto-Mod")
                    await message.channel.send(f"🔇 **{message.author.name}** has been timed out for spamming.")
                    self.spam_check[message.author.id] = [] # Reset
                except discord.Forbidden:
                    print(f"Could not timeout {message.author.name}")

    # --- MOD COMMANDS ---

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await self.dm_user(member, "Kicked", reason, interaction.user.name)
        await member.kick(reason=reason)
        
        embed = discord.Embed(description=f"👢 **{member.name}** has been kicked.", color=config.COLOR_RED)
        embed.add_field(name="Reason", value=reason)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await self.dm_user(member, "Banned", reason, interaction.user.name)
        await member.ban(reason=reason)
        
        embed = discord.Embed(description=f"🔨 **{member.name}** has been banned.", color=config.COLOR_RED)
        embed.add_field(name="Reason", value=reason)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(minutes="Duration in minutes")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        
        await self.dm_user(member, f"Timed Out ({minutes}m)", reason, interaction.user.name)
        
        embed = discord.Embed(description=f"⏳ **{member.name}** timed out for {minutes} minutes.", color=config.COLOR_GOLD)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
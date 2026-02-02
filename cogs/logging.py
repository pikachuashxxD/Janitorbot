import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {}

    # --- HELPER: Fetch Channel ID from Database ---
    def get_log_channel(self, guild, key):
        data = get_config(guild.id)
        channel_id = data.get(key)
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    # ====================================================
    # 1. JOIN LOGS (Entry Record)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.get_log_channel(member.guild, "log_join_id")
        if channel:
            # Calculate Account Age
            now = datetime.datetime.now(datetime.timezone.utc)
            created_at = member.created_at
            age = now - created_at
            
            # Nice formatting for age
            days = age.days
            age_str = f"{days} days ago" if days > 0 else "Today"

            embed = discord.Embed(description=f"📥 **{member.mention} Joined the Server**", color=config.COLOR_GREEN, timestamp=now)
            embed.set_author(name=f"{member.name}", icon_url=member.display_avatar.url)
            embed.add_field(name="Account Age", value=f"📅 Created {age_str}\n({discord.utils.format_dt(created_at, 'R')})", inline=False)
            embed.set_footer(text=f"User ID: {member.id} • Member #{member.guild.member_count}")
            await channel.send(embed=embed)

    # ====================================================
    # 2. LEAVE vs KICK LOGS (The Fix)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # We need to determine: Was this a Leave or a Kick?
        # We check the Audit Log for a "Kick" entry in the last 5 seconds.
        
        guild = member.guild
        is_kick = False
        kicker = None
        reason = "No reason provided"

        # Check Audit Logs
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    # Check if the kick happened just now (within 10 seconds)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if (now - entry.created_at).total_seconds() < 10:
                        is_kick = True
                        kicker = entry.user
                        reason = entry.reason or reason
                    break
        
        if is_kick:
            # ---> SEND TO MOD LOGS
            channel = self.get_log_channel(guild, "log_mod_id")
            if channel:
                embed = discord.Embed(description=f"👢 **{member.mention} was Kicked**", color=config.COLOR_RED, timestamp=datetime.datetime.now())
                embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                embed.add_field(name="Moderator", value=kicker.mention if kicker else "Unknown", inline=True)
                embed.add_field(name="Reason", value=reason, inline=True)
                embed.set_footer(text=f"User ID: {member.id}")
                await channel.send(embed=embed)
        else:
            # ---> SEND TO LEAVE LOGS
            channel = self.get_log_channel(guild, "log_leave_id")
            if channel:
                embed = discord.Embed(description=f"📤 **{member.mention} Left the Server**", color=config.COLOR_RED, timestamp=datetime.datetime.now())
                embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                # Show roles they had (excluding @everyone)
                roles = [r.name for r in member.roles if r.name != "@everyone"]
                role_str = ", ".join(roles) if roles else "None"
                embed.add_field(name="Roles", value=role_str, inline=False)
                embed.set_footer(text=f"User ID: {member.id} • Members: {guild.member_count}")
                await channel.send(embed=embed)

    # ====================================================
    # 3. BAN LOGS (Mod Logs)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = self.get_log_channel(guild, "log_mod_id")
        if not channel: return

        # Check who banned them
        banner = "Unknown"
        reason = "No reason provided"
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    banner = entry.user.mention
                    reason = entry.reason or reason
                    break

        embed = discord.Embed(description=f"🔨 **{user.mention} was Banned**", color=0x8b0000, timestamp=datetime.datetime.now()) # Dark Red
        embed.set_author(name=user.name, icon_url=user.display_avatar.url)
        embed.add_field(name="Moderator", value=banner, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        await channel.send(embed=embed)

    # ====================================================
    # 4. MESSAGE LOGS (Edit & Delete)
    # ====================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        channel = self.get_log_channel(message.guild, "log_msg_id")
        if channel:
            embed = discord.Embed(description=f"**Message sent by {message.author.mention} deleted in {message.channel.mention}**", color=config.COLOR_RED, timestamp=datetime.datetime.now())
            embed.set_author(name="Message Deleted", icon_url=message.author.display_avatar.url)
            content = message.content if message.content else "*[Image/Embed Only]*"
            embed.add_field(name=f"{config.EMOJIS['trash']} Content", value=f"```\n{content}\n```", inline=False)
            embed.set_footer(text=f"User ID: {message.author.id}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        channel = self.get_log_channel(before.guild, "log_msg_id")
        if channel:
            embed = discord.Embed(description=f"**Message edited in {before.channel.mention}** [Jump]({after.jump_url})", color=config.COLOR_BLUE, timestamp=datetime.datetime.now())
            embed.set_author(name=f"{before.author.name} Edited", icon_url=before.author.display_avatar.url)
            embed.add_field(name="❌ Before", value=f"{before.content}", inline=False)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name="✅ After", value=f"{after.content}", inline=False)
            embed.set_footer(text=f"User ID: {before.author.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 5. VOICE LOGS (Join, Leave, Move)
    # ====================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = self.get_log_channel(member.guild, "log_voice_id")
        if not channel: return

        # JOIN
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = datetime.datetime.now()
            embed = discord.Embed(description=f"**{member.mention} joined voice channel**", color=config.COLOR_GREEN, timestamp=datetime.datetime.now())
            embed.add_field(name="Channel", value=f"{config.EMOJIS['voice_join']} {after.channel.name}")
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

        # LEAVE
        elif before.channel is not None and after.channel is None:
            duration_str = "Unknown"
            if member.id in self.voice_sessions:
                start_time = self.voice_sessions.pop(member.id)
                duration = datetime.datetime.now() - start_time
                minutes = int(duration.total_seconds() // 60)
                hours = minutes // 60
                duration_str = f"{hours}h {minutes % 60}m" if hours > 0 else f"{minutes}m"

            embed = discord.Embed(description=f"**{member.mention} left voice channel**", color=config.COLOR_RED, timestamp=datetime.datetime.now())
            embed.add_field(name="Channel", value=f"{config.EMOJIS['voice_leave']} {before.channel.name}", inline=True)
            embed.add_field(name="Duration", value=f"⏱️ {duration_str}", inline=True)
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
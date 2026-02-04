import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {}

    def get_log_channel(self, guild, key):
        data = get_config(guild.id)
        channel_id = data.get(key)
        if not channel_id:
            channel_id = data.get("log_channel")
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    def format_time_ago(self, dt):
        if not dt: return "Unknown"
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - dt
        
        days = delta.days
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if days > 365: return f"{days // 365} years"
        if days > 0: return f"{days} days"
        if hours > 0: return f"{hours} hours"
        if minutes > 0: return f"{minutes} minutes"
        return f"{secs} seconds"

    # ====================================================
    # 1. JOIN LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.get_log_channel(member.guild, "log_join_id")
        if channel:
            embed = discord.Embed(
                description=f"Welcome {member.mention} to **{member.guild.name}**!", 
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name="Member Joined", icon_url=member.display_avatar.url)
            
            account_age = self.format_time_ago(member.created_at)
            embed.add_field(name="User", value=member.name, inline=True)
            embed.add_field(name="Account Created", value=f"{account_age} ago\n{discord.utils.format_dt(member.created_at, 'R')}", inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member Count: {member.guild.member_count} | User ID: {member.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 2. LEAVE & KICK LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        now = discord.utils.utcnow()
        is_kick = False
        kicker = None
        reason = "No reason provided"

        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    if (now - entry.created_at).total_seconds() < 10:
                        is_kick = True
                        kicker = entry.user
                        reason = entry.reason
                    break
        
        if is_kick:
            channel = self.get_log_channel(guild, "log_mod_id")
            if channel:
                # Uses config.EMOJIS['boot'] if you have one, or a fallback emoji
                boot_emoji = config.EMOJIS.get('boot', '👢')
                embed = discord.Embed(
                    title=f"{boot_emoji} Member Kicked", 
                    color=discord.Color.red(),
                    timestamp=now
                )
                embed.add_field(name="User", value=member.mention, inline=False)
                embed.add_field(name="Moderator", value=kicker.mention if kicker else "Unknown", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"User ID: {member.id}")
                await channel.send(embed=embed)
        else:
            channel = self.get_log_channel(guild, "log_leave_id")
            if channel:
                time_stayed = self.format_time_ago(member.joined_at)
                roles = [r.mention for r in member.roles if r.name != "@everyone"]
                roles_str = " ".join(roles) if roles else "None"

                embed = discord.Embed(
                    description=f"{member.mention} joined {time_stayed} ago", 
                    color=discord.Color.gold(),
                    timestamp=now
                )
                
                embed.set_author(name="Member left", icon_url=member.display_avatar.url)
                embed.add_field(name="Roles:", value=roles_str, inline=False)
                embed.set_footer(text=f"ID: {member.id}")
                await channel.send(embed=embed)

    # ====================================================
    # 3. VOICE LOGS (Now using Animated Emojis)
    # ====================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = self.get_log_channel(member.guild, "log_voice_id")
        if not channel: return
        
        now = datetime.datetime.now()

        # JOIN
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = now
            emoji = config.EMOJIS.get("voice_join", "🎤")
            
            embed = discord.Embed(
                description=f"{emoji} **{member.name}** joined **{after.channel.name}**",
                color=discord.Color.green(),
                timestamp=now
            )
            embed.set_author(name="Voice Join", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

        # LEAVE
        elif before.channel is not None and after.channel is None:
            duration_str = "0s"
            if member.id in self.voice_sessions:
                start_time = self.voice_sessions.pop(member.id)
                duration = now - start_time
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours}h {minutes}m {seconds}s"

            emoji = config.EMOJIS.get("voice_leave", "👋")
            
            embed = discord.Embed(
                description=f"{emoji} **{member.name}** left **{before.channel.name}**",
                color=discord.Color.red(),
                timestamp=now
            )
            embed.set_author(name="Voice Leave", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Duration", value=duration_str, inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

        # MOVED
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            emoji = config.EMOJIS.get("voice_move", "➡️")
            
            embed = discord.Embed(
                description=f"{emoji} **{member.name}** moved from **{before.channel.name}** to **{after.channel.name}**",
                color=discord.Color.gold(),
                timestamp=now
            )
            embed.set_author(name="Voice Move", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 4. DELETE LOGS (Now using Animated Emojis)
    # ====================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        channel = self.get_log_channel(message.guild, "log_delete_id")
        
        if channel:
            emoji = config.EMOJIS.get("trash", "🗑️")
            
            embed = discord.Embed(
                title=f"{emoji} Message Deleted", 
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Author", value=message.author.mention, inline=True)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            content = message.content if message.content else "*[Image/Media]*"
            embed.add_field(name="Content", value=content[:1024], inline=False)
            embed.set_footer(text=f"ID: {message.author.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 5. EDIT LOGS (Now using Animated Emojis)
    # ====================================================
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        channel = self.get_log_channel(before.guild, "log_edit_id")
        
        if channel:
            emoji = config.EMOJIS.get("edit", "✏️")
            
            embed = discord.Embed(
                title=f"{emoji} Message Edited", 
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Author", value=before.author.mention, inline=True)
            embed.add_field(name="Channel", value=before.channel.mention, inline=True)
            embed.add_field(name="Before", value=before.content[:1024], inline=False)
            embed.add_field(name="After", value=after.content[:1024], inline=False)
            embed.set_footer(text=f"ID: {before.author.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 6. MOD LOGS (TIMEOUTS)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not before.timed_out_until and after.timed_out_until:
            channel = self.get_log_channel(after.guild, "log_mod_id")
            
            if channel:
                moderator = "Unknown"
                reason = "No reason provided"
                if after.guild.me.guild_permissions.view_audit_log:
                    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == after.id:
                            moderator = entry.user.mention
                            reason = entry.reason or reason
                            break
                
                # Using a fallback hourglass emoji if 'timeout' isn't in your config yet
                emoji = config.EMOJIS.get("timeout", "⏳")

                embed = discord.Embed(
                    title=f"{emoji} Timeout Issued", 
                    color=discord.Color.gold(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="User", value=after.mention, inline=False)
                embed.add_field(name="Moderator", value=moderator, inline=True)
                embed.add_field(name="Duration", value=f"Until {discord.utils.format_dt(after.timed_out_until, 'f')}", inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"ID: {after.id}")
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Keeps track of when users join VC to calculate duration later
        self.voice_sessions = {}

    def get_log_channel(self, guild, key):
        """
        Fetches the specific log channel for an action (e.g., 'log_join_id').
        If that specific channel isn't set, falls back to the main 'log_channel'.
        """
        data = get_config(guild.id)
        channel_id = data.get(key)
        if not channel_id:
            channel_id = data.get("log_channel")
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    def format_time_ago(self, dt):
        """Calculates the time difference string."""
        if not dt: return "Unknown"
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - dt
        
        days = delta.days
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if days > 365: return f"{days // 365} years ago"
        if days > 0: return f"{days} days ago"
        if hours > 0: return f"{hours} hours ago"
        if minutes > 0: return f"{minutes} minutes ago"
        return f"{secs} seconds ago"

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
            embed.add_field(name="Account Created", value=f"{account_age}\n{discord.utils.format_dt(member.created_at, 'R')}", inline=True)
            
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

        # Check Audit Logs to see if the user was Kicked
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    # If kick happened in the last 10 seconds, assume it corresponds to this leave event
                    if (now - entry.created_at).total_seconds() < 10:
                        is_kick = True
                        kicker = entry.user
                        reason = entry.reason
                    break
        
        if is_kick:
            # --- KICK LOG (Red) ---
            channel = self.get_log_channel(guild, "log_mod_id")
            if channel:
                embed = discord.Embed(
                    title="👢 Member Kicked", 
                    color=discord.Color.red(),
                    timestamp=now
                )
                embed.add_field(name="User", value=member.mention, inline=False)
                embed.add_field(name="Moderator", value=kicker.mention if kicker else "Unknown", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"User ID: {member.id}")
                await channel.send(embed=embed)
        else:
            # --- LEAVE LOG (Gold/Yellow - Matches Screenshot) ---
            channel = self.get_log_channel(guild, "log_leave_id")
            if channel:
                # Calculate how long they stayed
                time_stayed = self.format_time_ago(member.joined_at)
                
                # List roles (excluding @everyone)
                roles = [r.mention for r in member.roles if r.name != "@everyone"]
                roles_str = " ".join(roles) if roles else "None"

                embed = discord.Embed(
                    description=f"{member.mention} joined {time_stayed} ago", 
                    color=discord.Color.gold(), # Matches the screenshot color
                    timestamp=now
                )
                
                # Uses the USER'S Profile Picture
                embed.set_author(name="Member left", icon_url=member.display_avatar.url)
                
                embed.add_field(name="Roles:", value=roles_str, inline=False)
                embed.set_footer(text=f"ID: {member.id}")
                await channel.send(embed=embed)

    # ====================================================
    # 3. VOICE LOGS (Duration Tracking)
    # ====================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = self.get_log_channel(member.guild, "log_voice_id")
        if not channel: return
        
        now = datetime.datetime.now()

        # JOIN
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = now
            embed = discord.Embed(
                description=f"🎤 **{member.name}** joined **{after.channel.name}**",
                color=discord.Color.green(),
                timestamp=now
            )
            embed.set_author(name="Voice Join", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

        # LEAVE
        elif before.channel is not None and after.channel is None:
            duration_str = "0s"
            # Calculate duration
            if member.id in self.voice_sessions:
                start_time = self.voice_sessions.pop(member.id)
                duration = now - start_time
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours}h {minutes}m {seconds}s"

            embed = discord.Embed(
                description=f"👋 **{member.name}** left **{before.channel.name}**",
                color=discord.Color.red(),
                timestamp=now
            )
            embed.set_author(name="Voice Leave", icon_url=member.display_avatar.url)
            embed.add_field(name="Duration", value=duration_str, inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

        # MOVED
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(
                description=f"➡️ **{member.name}** moved from **{before.channel.name}** to **{after.channel.name}**",
                color=discord.Color.gold(),
                timestamp=now
            )
            embed.set_author(name="Voice Move", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 4. DELETE LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        channel = self.get_log_channel(message.guild, "log_delete_id")
        
        if channel:
            embed = discord.Embed(
                title="🗑️ Message Deleted", 
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
    # 5. EDIT LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        channel = self.get_log_channel(before.guild, "log_edit_id")
        
        if channel:
            embed = discord.Embed(
                title="✏️ Message Edited", 
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
        # Check if Timeout was added
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

                embed = discord.Embed(
                    title="⏳ Timeout Issued", 
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
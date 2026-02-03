import discord
from discord.ext import commands
import datetime
import config
from utils.database import get_config

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {}

    # --- HELPER: Get Log Channel ---
    def get_log_channel(self, guild, key):
        data = get_config(guild.id)
        channel_id = data.get(key)
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    # ====================================================
    # 1. JOIN LOGS (Already had big pic, keeping it)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.get_log_channel(member.guild, "log_join_id")
        if channel:
            # Calculate Account Age
            now = datetime.datetime.now(datetime.timezone.utc)
            created_at = member.created_at
            age = now - created_at
            days = age.days
            age_str = f"{days} days ago" if days > 0 else "Today"

            # See for style reference
            embed = discord.Embed(description=f"Welcome {member.mention} to **{member.guild.name}**!", color=config.COLOR_GREEN)
            embed.set_author(name="Member Joined", icon_url=config.EMOJIS['anim_join'] if '<a:' in config.EMOJIS['anim_join'] else None)
            
            embed.add_field(name="User", value=member.name, inline=True)
            embed.add_field(name="Account Created", value=f"{age_str}\n({discord.utils.format_dt(created_at, 'R')})", inline=True)
            
            # Large Thumbnail
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member Count: {member.guild.member_count} | ID: {member.id} • {discord.utils.format_dt(datetime.datetime.now())}")
            await channel.send(embed=embed)

    # ====================================================
    # 2. LEAVE & KICK LOGS (Updated with Big Pics)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        is_kick = False
        kicker = None
        reason = "No reason provided"

        # Audit log check for Kick
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    if (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 10:
                        is_kick = True
                        kicker = entry.user
                        reason = entry.reason
                    break
        
        if is_kick:
            # KICK LOG
            channel = self.get_log_channel(guild, "log_mod_id")
            if channel:
                embed = discord.Embed(title=f"{config.EMOJIS['boot']} Member Kicked", color=config.COLOR_RED)
                embed.add_field(name="User", value=member.mention, inline=False)
                embed.add_field(name="Moderator", value=kicker.mention if kicker else "Unknown", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                # Large Thumbnail
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"ID: {member.id} • {discord.utils.format_dt(datetime.datetime.now())}")
                await channel.send(embed=embed)
        else:
            # LEAVE LOG
            channel = self.get_log_channel(guild, "log_leave_id")
            if channel:
                embed = discord.Embed(description=f"**{member.name}** has left the server.", color=config.COLOR_RED)
                embed.set_author(name="Member Left", icon_url=config.EMOJIS['anim_leave'] if '<a:' in config.EMOJIS['anim_leave'] else None)
                # Large Thumbnail
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member Count: {guild.member_count} | ID: {member.id} • {discord.utils.format_dt(datetime.datetime.now())}")
                await channel.send(embed=embed)

    # ====================================================
    # 3. MESSAGE LOGS (Updated with Big Pics & Animations)
    # ====================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        channel = self.get_log_channel(message.guild, "log_msg_id")
        
        if channel:
            # See for style reference
            embed = discord.Embed(title=f"{config.EMOJIS['anim_delete']} Message Deleted", color=config.COLOR_RED)
            
            embed.add_field(name="Author", value=message.author.mention, inline=True)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            
            content = message.content if message.content else "*[Image/Media]*"
            embed.add_field(name="Content", value=content, inline=False)
            
            # Large Thumbnail
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text=f"User ID: {message.author.id} • {discord.utils.format_dt(datetime.datetime.now())}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        channel = self.get_log_channel(before.guild, "log_msg_id")
        
        if channel:
            # See for style reference
            embed = discord.Embed(title=f"{config.EMOJIS['anim_edit']} Message Edited", color=config.COLOR_BLUE)
            
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)

            # Large Thumbnail
            embed.set_thumbnail(url=before.author.display_avatar.url)
            embed.set_footer(text=f"Channel: #{before.channel.name} | User ID: {before.author.id} • {discord.utils.format_dt(datetime.datetime.now())}")
            await channel.send(embed=embed)

    # ====================================================
    # 4. VOICE LOGS (Now includes MOVED!)
    # ====================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = self.get_log_channel(member.guild, "log_voice_id")
        if not channel: return

        # JOIN
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = datetime.datetime.now()
            # See for style reference
            embed = discord.Embed(description=f"**{member.mention} joined voice channel**", color=config.COLOR_GREEN)
            embed.set_author(name="Voice Join", icon_url=config.EMOJIS['anim_join'] if '<a:' in config.EMOJIS['anim_join'] else None)
            embed.add_field(name="Channel", value=after.channel.name, inline=True)
            # Large Thumbnail
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"{discord.utils.format_dt(datetime.datetime.now())}")
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

            # See for style reference
            embed = discord.Embed(description=f"**{member.mention} left voice channel**", color=config.COLOR_RED)
            embed.set_author(name="Voice Leave", icon_url=config.EMOJIS['anim_leave'] if '<a:' in config.EMOJIS['anim_leave'] else None)
            embed.add_field(name="Channel", value=before.channel.name, inline=True)
            embed.add_field(name="Duration", value=duration_str, inline=True)
            # Large Thumbnail
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"{discord.utils.format_dt(datetime.datetime.now())}")
            await channel.send(embed=embed)

        # --- NEW: MOVED LOG ---
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(description=f"**{member.mention} moved voice channels**", color=config.COLOR_GOLD)
            embed.set_author(name="Voice Moved", icon_url=config.EMOJIS['anim_move'] if '<a:' in config.EMOJIS['anim_move'] else None)
            
            embed.add_field(name="From", value=before.channel.name, inline=True)
            embed.add_field(name="To", value=after.channel.name, inline=True)
            
            # Large Thumbnail
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"{discord.utils.format_dt(datetime.datetime.now())}")
            await channel.send(embed=embed)

    # ====================================================
    # 5. MOD LOGS (Timeout Update)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Check for timeout change
        if not before.timed_out_until and after.timed_out_until:
            channel = self.get_log_channel(after.guild, "log_mod_id")
            if channel:
                # Try to fetch audit log for Moderator & Reason
                moderator = "Unknown"
                reason = "No reason provided"
                if after.guild.me.guild_permissions.view_audit_log:
                    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == after.id:
                            moderator = entry.user.mention
                            reason = entry.reason or reason
                            break

                # See for style reference
                embed = discord.Embed(title=f"{config.EMOJIS['timeout']} Timeout Update", color=config.COLOR_GOLD)
                embed.add_field(name="User", value=after.mention, inline=False)
                embed.add_field(name="Moderator", value=moderator, inline=True)
                embed.add_field(name="Action", value=f"Timed out until {discord.utils.format_dt(after.timed_out_until, 'f')}", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                # Large Thumbnail
                embed.set_thumbnail(url=after.display_avatar.url)
                embed.set_footer(text=f"{discord.utils.format_dt(datetime.datetime.now())}")
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
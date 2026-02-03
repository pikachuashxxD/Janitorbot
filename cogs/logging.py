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
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    # ====================================================
    # 1. JOIN LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.get_log_channel(member.guild, "log_join_id")
        if channel:
            now = datetime.datetime.now()
            age = now - member.created_at.replace(tzinfo=None)
            days = age.days
            age_str = f"{days} days ago" if days > 0 else "Today"

            # Added 'timestamp=now' for clean date display
            embed = discord.Embed(
                description=f"Welcome {member.mention} to **{member.guild.name}**!", 
                color=config.COLOR_GREEN,
                timestamp=now
            )
            embed.set_author(name="Member Joined", icon_url=member.display_avatar.url)
            
            embed.add_field(name="User", value=member.name, inline=True)
            embed.add_field(name="Account Created", value=f"{age_str}\n{discord.utils.format_dt(member.created_at, 'R')}", inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            # Footer is now CLEAN: Just the IDs
            embed.set_footer(text=f"Member Count: {member.guild.member_count} | User ID: {member.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 2. LEAVE & KICK LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        now = datetime.datetime.now()
        is_kick = False
        kicker = None
        reason = "No reason provided"

        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    if (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 10:
                        is_kick = True
                        kicker = entry.user
                        reason = entry.reason
                    break
        
        if is_kick:
            channel = self.get_log_channel(guild, "log_mod_id")
            if channel:
                embed = discord.Embed(
                    title=f"{config.EMOJIS['boot']} Member Kicked", 
                    color=config.COLOR_RED,
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
                embed = discord.Embed(
                    description=f"**{member.name}** has left the server.", 
                    color=config.COLOR_RED,
                    timestamp=now
                )
                embed.set_author(name="Member Left", icon_url=member.display_avatar.url)
                embed.set_thumbnail(url=member.display_avatar.url)
                
                embed.set_footer(text=f"Member Count: {guild.member_count} | User ID: {member.id}")
                await channel.send(embed=embed)

    # ====================================================
    # 3. VOICE LOGS
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
                description=f"**{member.mention} joined voice channel**", 
                color=config.COLOR_GREEN,
                timestamp=now
            )
            embed.set_author(name="Voice Join", icon_url=member.display_avatar.url)
            
            embed.add_field(name=f"{config.EMOJIS['voice_join']} Channel", value=after.channel.name, inline=True)
            embed.add_field(name="Time", value=discord.utils.format_dt(now, 't'), inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)

        # LEAVE
        elif before.channel is not None and after.channel is None:
            duration_str = "Unknown"
            if member.id in self.voice_sessions:
                start_time = self.voice_sessions.pop(member.id)
                duration = now - start_time
                
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                if hours > 0:
                    duration_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    duration_str = f"{minutes}m {seconds}s"
                else:
                    duration_str = f"{seconds}s"

            embed = discord.Embed(
                description=f"**{member.mention} left voice channel**", 
                color=config.COLOR_RED,
                timestamp=now
            )
            embed.set_author(name="Voice Leave", icon_url=member.display_avatar.url)
            
            embed.add_field(name=f"{config.EMOJIS['voice_leave']} Channel", value=before.channel.name, inline=True)
            embed.add_field(name="Duration", value=duration_str, inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)

        # MOVED
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(
                description=f"**{member.mention} moved voice channels**", 
                color=config.COLOR_GOLD,
                timestamp=now
            )
            embed.set_author(name="Voice Moved", icon_url=member.display_avatar.url)
            
            embed.add_field(name="From", value=before.channel.name, inline=True)
            embed.add_field(name=f"{config.EMOJIS['voice_move']} To", value=after.channel.name, inline=True)
            embed.add_field(name="Time", value=discord.utils.format_dt(now, 't'), inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 4. DELETE LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        channel = self.get_log_channel(message.guild, "log_delete_id")
        now = datetime.datetime.now()
        
        if channel:
            embed = discord.Embed(
                title=f"{config.EMOJIS['trash']} Message Deleted", 
                color=config.COLOR_RED,
                timestamp=now
            )
            embed.add_field(name="Author", value=message.author.mention, inline=True)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            content = message.content if message.content else "*[Image/Media]*"
            embed.add_field(name="Content", value=content, inline=False)
            
            embed.set_footer(text=f"User ID: {message.author.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 5. EDIT LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        channel = self.get_log_channel(before.guild, "log_edit_id")
        now = datetime.datetime.now()
        
        if channel:
            embed = discord.Embed(
                title=f"{config.EMOJIS['edit']} Message Edited", 
                color=config.COLOR_BLUE,
                timestamp=now
            )
            embed.set_author(name=before.author.name, icon_url=before.author.display_avatar.url)
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            
            embed.set_footer(text=f"Channel: #{before.channel.name} | User ID: {before.author.id}")
            await channel.send(embed=embed)

    # ====================================================
    # 6. MOD LOGS
    # ====================================================
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not before.timed_out_until and after.timed_out_until:
            channel = self.get_log_channel(after.guild, "log_mod_id")
            now = datetime.datetime.now()
            
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
                    title=f"{config.EMOJIS['timeout']} Timeout Update", 
                    color=config.COLOR_GOLD,
                    timestamp=now
                )
                embed.add_field(name="User", value=after.mention, inline=False)
                embed.add_field(name="Moderator", value=moderator, inline=True)
                embed.add_field(name="Action", value=f"Timed out until {discord.utils.format_dt(after.timed_out_until, 'f')}", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                
                embed.set_footer(text=f"User ID: {after.id}")
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
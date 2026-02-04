import discord
from discord.ext import commands
import datetime
from utils.database import get_config

class UserUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild, key):
        """
        Fetches channel for specific key.
        Fallback: If specific key isn't set, try Main Log Channel.
        """
        data = get_config(guild.id)
        channel_id = data.get(key)
        
        if not channel_id:
            channel_id = data.get("log_channel")
            
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    # ====================================================
    # 1. SERVER-SPECIFIC UPDATES (Nicknames, Server Avatars, Roles)
    # ====================================================
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.timed_out_until != after.timed_out_until:
            return

        now = discord.utils.utcnow()
        guild = before.guild

        # --- NICKNAME ---
        if before.nick != after.nick:
            channel = self.get_log_channel(guild, "log_nickname_id")
            if channel:
                embed = discord.Embed(
                    title="🏷️ Nickname Changed",
                    color=discord.Color.blue(),
                    timestamp=now
                )
                embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                
                before_nick = before.nick if before.nick else "[None] (Username)"
                after_nick = after.nick if after.nick else "[None] (Username)"

                embed.add_field(name="Before", value=f"`{before_nick}`", inline=True)
                embed.add_field(name="After", value=f"`{after_nick}`", inline=True)
                embed.set_footer(text=f"ID: {after.id}")
                await channel.send(embed=embed)

        # --- SERVER AVATAR ---
        # This catches changes when a user uploads a specific "Server Profile" picture
        if before.guild_avatar != after.guild_avatar:
            channel = self.get_log_channel(guild, "log_avatar_id")
            if channel:
                embed = discord.Embed(
                    title="🖼️ Server Avatar Changed",
                    description=f"{after.mention} updated their server profile picture.",
                    color=discord.Color.gold(),
                    timestamp=now
                )
                embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                
                # Use display_avatar to show what is currently visible
                embed.set_thumbnail(url=before.display_avatar.url)
                embed.set_image(url=after.display_avatar.url)
                
                embed.set_footer(text=f"ID: {after.id}")
                await channel.send(embed=embed)

        # --- ROLES ---
        if before.roles != after.roles:
            channel = self.get_log_channel(guild, "log_role_id")
            if channel:
                before_roles = set(before.roles)
                after_roles = set(after.roles)

                added_roles = after_roles - before_roles
                if added_roles:
                    roles_str = ", ".join([r.mention for r in added_roles])
                    embed = discord.Embed(
                        title="📈 Role Added",
                        description=f"{after.mention} was given the role(s): {roles_str}",
                        color=discord.Color.green(),
                        timestamp=now
                    )
                    embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                    embed.set_footer(text=f"ID: {after.id}")
                    await channel.send(embed=embed)

                removed_roles = before_roles - after_roles
                if removed_roles:
                    roles_str = ", ".join([r.mention for r in removed_roles])
                    embed = discord.Embed(
                        title="📉 Role Removed",
                        description=f"{after.mention} lost the role(s): {roles_str}",
                        color=discord.Color.red(),
                        timestamp=now
                    )
                    embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                    embed.set_footer(text=f"ID: {after.id}")
                    await channel.send(embed=embed)

    # ====================================================
    # 2. GLOBAL UPDATES (Main Profile Picture)
    # ====================================================
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        # Check if the global avatar changed
        if before.avatar != after.avatar:
            now = discord.utils.utcnow()
            
            # Since 'User' updates are global, we need to check which shared servers config logging for this
            for guild in self.bot.guilds:
                # Check if this user is in the guild
                member = guild.get_member(after.id)
                if member:
                    # Check if this specific guild has avatar logging enabled
                    channel = self.get_log_channel(guild, "log_avatar_id")
                    if channel:
                        embed = discord.Embed(
                            title="🖼️ Global Avatar Changed",
                            description=f"{member.mention} updated their global profile picture.",
                            color=discord.Color.gold(),
                            timestamp=now
                        )
                        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                        
                        # Handle cases where before/after might be None (default avatar)
                        old_url = before.avatar.url if before.avatar else before.default_avatar.url
                        new_url = after.avatar.url if after.avatar else after.default_avatar.url

                        embed.set_thumbnail(url=old_url)
                        embed.set_image(url=new_url)
                        
                        embed.set_footer(text=f"ID: {member.id}")
                        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserUpdates(bot))
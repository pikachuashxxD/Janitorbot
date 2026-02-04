import discord
from discord.ext import commands
import datetime
from utils.database import get_config

class UserUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        data = get_config(guild.id)
        # Looks for the specific "profile" channel first
        channel_id = data.get("log_profile_id") 
        
        # Fallback: If no profile channel, try the generic log channel
        if not channel_id:
            channel_id = data.get("log_channel")
            
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Skip timeout updates (handled by logging.py)
        if before.timed_out_until != after.timed_out_until:
            return

        channel = self.get_log_channel(before.guild)
        if not channel: return

        now = discord.utils.utcnow()

        # ====================================================
        # 1. NICKNAME CHANGES
        # ====================================================
        if before.nick != after.nick:
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

        # ====================================================
        # 2. PROFILE PICTURE CHANGES
        # ====================================================
        if before.display_avatar.url != after.display_avatar.url:
            embed = discord.Embed(
                title="🖼️ Avatar Changed",
                description=f"{after.mention} updated their profile picture.",
                color=discord.Color.gold(),
                timestamp=now
            )
            embed.set_author(name=after.name, icon_url=after.display_avatar.url)
            
            embed.set_thumbnail(url=before.display_avatar.url)
            embed.set_image(url=after.display_avatar.url)
            
            embed.set_footer(text=f"ID: {after.id}")
            await channel.send(embed=embed)

        # ====================================================
        # 3. ROLE CHANGES (Added / Removed)
        # ====================================================
        if before.roles != after.roles:
            # key: id, value: role_object
            before_roles = set(before.roles)
            after_roles = set(after.roles)

            # Check for Added Roles
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

            # Check for Removed Roles
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

async def setup(bot):
    await bot.add_cog(UserUpdates(bot))
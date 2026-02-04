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
        
        # 1. Try specific key (e.g. log_nickname_id)
        channel_id = data.get(key)
        
        # 2. Fallback to MAIN log channel
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

        now = discord.utils.utcnow()

        # ====================================================
        # 1. NICKNAME CHANGES
        # ====================================================
        if before.nick != after.nick:
            channel = self.get_log_channel(before.guild, "log_nickname_id")
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

        # ====================================================
        # 2. PROFILE PICTURE CHANGES (Fixed)
        # ====================================================
        # We compare the URL strings now. This is safer than comparing objects.
        if before.display_avatar.url != after.display_avatar.url:
            print(f"[DEBUG] Avatar change detected for {after.name}") # Check your console for this!
            
            channel = self.get_log_channel(before.guild, "log_avatar_id")
            if channel:
                embed = discord.Embed(
                    title="🖼️ Avatar Changed",
                    description=f"{after.mention} updated their profile picture.",
                    color=discord.Color.gold(),
                    timestamp=now
                )
                embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                
                # Thumbnail = Old Pic
                embed.set_thumbnail(url=before.display_avatar.url)
                
                # Big Image = New Pic
                embed.set_image(url=after.display_avatar.url)
                
                embed.set_footer(text=f"ID: {after.id}")
                await channel.send(embed=embed)

        # ====================================================
        # 3. ROLE CHANGES
        # ====================================================
        if before.roles != after.roles:
            channel = self.get_log_channel(before.guild, "log_role_id")
            if channel:
                before_roles = set(before.roles)
                after_roles = set(after.roles)

                # Added
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

                # Removed
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
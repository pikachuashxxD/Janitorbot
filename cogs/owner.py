import discord
from discord import app_commands
from discord.ext import commands
import datetime
import traceback
import config

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Listen for errors globally
        self.bot.tree.on_error = self.on_app_command_error

    # --- CHECK: IS OWNER? ---
    # This function checks if the user running the command is YOU.
    def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == config.OWNER_ID

    # ====================================================
    # 1. SYNC COMMAND (Text Command)
    # ====================================================
    # We use a standard text command (!sync) here because if Slash Commands 
    # break, you need a backup way to fix them.
    @commands.command(name="sync")
    async def sync(self, ctx):
        if ctx.author.id != config.OWNER_ID:
            return
        
        msg = await ctx.send("🔄 Syncing commands...")
        try:
            synced = await self.bot.tree.sync()
            await msg.edit(content=f"✅ Synced **{len(synced)}** commands globally!")
        except Exception as e:
            await msg.edit(content=f"❌ Sync failed: {e}")

    # ====================================================
    # 2. OWNER GROUP (Slash Commands)
    # ====================================================
    owner_group = app_commands.Group(name="owner", description="Bot Owner Controls")

    @owner_group.command(name="status", description="Change the bot's activity status")
    async def change_status(self, interaction: discord.Interaction, activity_type: str, text: str):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌ You are not the owner.", ephemeral=True)

        # Map string to Discord ActivityType
        types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing
        }
        
        act = types.get(activity_type.lower(), discord.ActivityType.playing)
        await self.bot.change_presence(activity=discord.Activity(type=act, name=text))
        await interaction.response.send_message(f"✅ Status changed to: **{activity_type.capitalize()} {text}**", ephemeral=True)

    @owner_group.command(name="servers", description="List top 10 servers by member count")
    async def servers(self, interaction: discord.Interaction):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌ You are not the owner.", ephemeral=True)

        # Sort guilds by member count
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        
        desc = ""
        for i, g in enumerate(guilds[:10], 1):
            desc += f"**{i}. {g.name}**\n👤 {g.member_count} Members | 🆔 `{g.id}`\n\n"

        embed = discord.Embed(title=f"🤖 Bot is in {len(self.bot.guilds)} Servers", description=desc, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @owner_group.command(name="leave_server", description="Force the bot to leave a server")
    async def leave_server(self, interaction: discord.Interaction, server_id: str):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌ You are not the owner.", ephemeral=True)

        try:
            guild = self.bot.get_guild(int(server_id))
            if not guild:
                return await interaction.response.send_message("❌ Server not found.", ephemeral=True)
            
            await guild.leave()
            await interaction.response.send_message(f"✅ Left server **{guild.name}**.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    # ====================================================
    # 3. SYSTEM LOGGING (Joins, Leaves, Errors)
    # ====================================================
    def get_log_channel(self):
        if hasattr(config, 'BOT_LOG_CHANNEL'):
            return self.bot.get_channel(config.BOT_LOG_CHANNEL)
        return None

    # Log Errors
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Notify User
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred.", ephemeral=True)

        # Log to Channel
        channel = self.get_log_channel()
        if channel:
            embed = discord.Embed(title="⚠️ Bot Error", color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.add_field(name="Command", value=f"/{interaction.command.name}" if interaction.command else "Unknown")
            embed.add_field(name="User", value=f"{interaction.user.name}")
            
            # Traceback (Shortened)
            error_msg = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            embed.description = f"```py\n{error_msg[:1000]}```"
            await channel.send(embed=embed)
        else:
            print(f"Error: {error}")

    # Log Join
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = self.get_log_channel()
        if channel:
            embed = discord.Embed(title="📈 Joined Server", color=discord.Color.green(), timestamp=datetime.datetime.now())
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(name="Name", value=guild.name)
            embed.add_field(name="Members", value=str(guild.member_count))
            embed.add_field(name="Owner", value=f"{guild.owner.name} ({guild.owner_id})")
            await channel.send(embed=embed)

    # Log Leave
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self.get_log_channel()
        if channel:
            embed = discord.Embed(title="📉 Left Server", color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.add_field(name="Name", value=guild.name)
            embed.add_field(name="Members", value=str(guild.member_count))
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Owner(bot))
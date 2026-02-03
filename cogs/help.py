import discord
from discord import app_commands, ui
from discord.ext import commands

class HelpSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Clan Commands", description="Create, Join, Manage Clans", value="clan"),
            discord.SelectOption(label="⚙️ Admin & Owner", description="Setup and Owner controls", value="admin"),
            discord.SelectOption(label="🎮 General", description="Teams, AFK, etc.", value="general")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        embed = discord.Embed(color=0x3498db)

        if val == "clan":
            embed.title = "🛡️ Clan System Commands"
            embed.description = "Commands for creating and managing clans."
            embed.add_field(name="/create_clan", value="Request to create a new clan (Requires Role)", inline=False)
            embed.add_field(name="/apply_clan", value="Apply to join an existing clan", inline=False)
            embed.add_field(name="/leave_clan", value="Leave your current clan", inline=False)
            embed.add_field(name="/clan_info", value="View info about the current clan", inline=False)
            embed.add_field(name="/clan_list", value="View leaderboard of top clans", inline=False)
            embed.add_field(name="👑 Leader Only", value="`/clan_kick`, `/transfer_ownership`, `/disband_clan`", inline=False)

        elif val == "admin":
            embed.title = "⚙️ Admin & Owner Commands"
            embed.description = "Commands for server management."
            embed.add_field(name="/setup logs", value="Configure log channels", inline=False)
            embed.add_field(name="/setup stream", value="Configure streamer alerts", inline=False)
            embed.add_field(name="/setup_clan_system", value="Initialize Clan Categories", inline=False)
            embed.add_field(name="/owner status", value="Change Bot Presence", inline=False)
            embed.add_field(name="/owner backup", value="Backup Clan Database", inline=False)
            embed.add_field(name="!sync", value="Sync Slash Commands (Text Command)", inline=False)

        elif val == "general":
            embed.title = "🎮 General Commands"
            embed.description = "Utilities for everyone."
            embed.add_field(name="/teams", value="Split names into two teams", inline=False)
            embed.add_field(name="/afk", value="Set your status to AFK", inline=False)
            embed.add_field(name="/setup welcome", value="Set welcome channel", inline=False)

        await interaction.response.edit_message(embed=embed)

class HelpView(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show bot commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Bot Help Menu", description="Select a category below to view commands.", color=0x3498db)
        await interaction.response.send_message(embed=embed, view=HelpView())

async def setup(bot):
    await bot.add_cog(Help(bot))
import discord
from discord import app_commands
from discord.ext import commands
import random
import config

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_data = {} # {user_id: reason}

    # --- AFK COMMAND ---
    @app_commands.command(name="afk", description="Set your status to AFK")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        user = interaction.user
        self.afk_data[user.id] = reason
        
        # Try to change nickname
        try:
            original_name = user.display_name
            await user.edit(nick=f"[AFK] {original_name}")
            msg = f"💤 I've set your AFK: **{reason}**"
        except discord.Forbidden:
            msg = f"💤 I've set your AFK: **{reason}** (I couldn't change your nickname due to permissions)."
        
        await interaction.response.send_message(msg, ephemeral=True)

    # --- AFK LISTENERS ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # 1. Remove AFK if user types
        if message.author.id in self.afk_data:
            reason = self.afk_data.pop(message.author.id)
            try:
                # Remove [AFK] tag if it exists
                clean_name = message.author.display_name.replace("[AFK] ", "")
                await message.author.edit(nick=clean_name)
            except discord.Forbidden:
                pass
            
            await message.channel.send(f"👋 Welcome back **{message.author.mention}**, I removed your AFK.", delete_after=5)

        # 2. Check if mentioned user is AFK
        if message.mentions:
            for user in message.mentions:
                if user.id in self.afk_data:
                    reason = self.afk_data[user.id]
                    await message.channel.send(f"💤 **{user.display_name}** is currently AFK: {reason}")

    # --- TEAM GENERATOR (Pika vs Skurr) ---
    @app_commands.command(name="teams", description="Randomly split a list of names into 2 teams")
    @app_commands.describe(names="List of names separated by commas or spaces")
    async def teams(self, interaction: discord.Interaction, names: str):
        """
        Usage: /teams names: Pika, Ash, Misty, Brock
        """
        # 1. Clean and split the input
        # Replace commas with spaces to handle both formats, then split
        player_list = [name.strip() for name in names.replace(",", " ").split() if name.strip()]

        if len(player_list) < 2:
            await interaction.response.send_message("❌ I need at least 2 names to make teams!", ephemeral=True)
            return

        # 2. Shuffle
        random.shuffle(player_list)

        # 3. Split
        midpoint = len(player_list) // 2
        team_1 = player_list[:midpoint]
        team_2 = player_list[midpoint:]

        # 4. Display
        embed = discord.Embed(title="⚔️ Team Generator", color=0x3498db)
        embed.add_field(name=f"🔴 Team Red ({len(team_1)})", value="\n".join(team_1) or "None", inline=True)
        embed.add_field(name=f"🔵 Team Blue ({len(team_2)})", value="\n".join(team_2) or "None", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utils(bot))
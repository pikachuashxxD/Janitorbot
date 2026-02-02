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
    @app_commands.command(name="teams", description="Randomly split voice channel users into teams")
    async def teams(self, interaction: discord.Interaction):
        # check if user is in VC
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a Voice Channel to use this!", ephemeral=True)
            return

        # Get members
        members = interaction.user.voice.channel.members
        if len(members) < 2:
            await interaction.response.send_message("❌ Need at least 2 people to make teams!", ephemeral=True)
            return

        # Shuffle
        random.shuffle(members)
        
        # Split
        mid = len(members) // 2
        team_pika = members[:mid]
        team_skurr = members[mid:]

        # Create Embed
        embed = discord.Embed(title="⚔️ Team Generator", color=config.COLOR_GOLD)
        
        pika_names = "\n".join([m.mention for m in team_pika])
        skurr_names = "\n".join([m.mention for m in team_skurr])

        embed.add_field(name="⚡ Team Pika", value=pika_names if pika_names else "No one", inline=True)
        embed.add_field(name="💀 Team Skurr", value=skurr_names if skurr_names else "No one", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
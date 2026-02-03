import discord
from discord import app_commands
from discord.ext import commands
import random

# Class name is "General"
class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Simple storage for AFK users: {user_id: "reason"}
        self.afk_data = {}

    # ====================================================
    # 1. TEAMS COMMAND (Fixed)
    # ====================================================
    @app_commands.command(name="teams", description="Randomly split a list of names into 2 teams")
    @app_commands.describe(names="List of names separated by commas or spaces")
    async def teams(self, interaction: discord.Interaction, names: str):
        """
        Usage: /teams names: Pika, Ash, Misty, Brock
        """
        player_list = [name.strip() for name in names.replace(",", " ").split() if name.strip()]

        if len(player_list) < 2:
            await interaction.response.send_message("❌ I need at least 2 names to make teams!", ephemeral=True)
            return

        random.shuffle(player_list)

        midpoint = len(player_list) // 2
        team_1 = player_list[:midpoint]
        team_2 = player_list[midpoint:]

        embed = discord.Embed(title="⚔️ Team Generator", color=0x3498db)
        embed.add_field(name=f"🔴 Team Red ({len(team_1)})", value="\n".join(team_1) or "None", inline=True)
        embed.add_field(name=f"🔵 Team Blue ({len(team_2)})", value="\n".join(team_2) or "None", inline=True)

        await interaction.response.send_message(embed=embed)

    # ====================================================
    # 2. AFK COMMAND
    # ====================================================
    @app_commands.command(name="afk", description="Set your status to AFK")
    @app_commands.describe(reason="Why are you going AFK?")
    async def afk(self, interaction: discord.Interaction, reason: str = "I'll be back soon!"):
        user = interaction.user
        
        # 1. Save AFK status
        self.afk_data[user.id] = reason

        # 2. Try to change nickname to [AFK] Name
        try:
            current_name = user.display_name
            if not current_name.startswith("[AFK]"):
                new_name = f"[AFK] {current_name}"
                # Limit to 32 chars (Discord limit)
                await user.edit(nick=new_name[:32])
        except discord.Forbidden:
            pass # Bot can't change owner's nickname or higher roles

        await interaction.response.send_message(f"💤 **{user.name}** is now AFK: {reason}")

    # ====================================================
    # 3. AFK LISTENERS (Auto-Remove & Auto-Reply)
    # ====================================================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # A. Check if the person TYPING is AFK -> Remove AFK
        if message.author.id in self.afk_data:
            del self.afk_data[message.author.id]
            
            # Remove [AFK] from nickname
            try:
                name = message.author.display_name
                if name.startswith("[AFK] "):
                    await message.author.edit(nick=name[6:])
            except discord.Forbidden:
                pass

            await message.channel.send(f"👋 Welcome back, {message.author.mention}! I removed your AFK status.", delete_after=5)

        # B. Check if an AFK person was MENTIONED -> Reply with Reason
        if message.mentions:
            for mentioned_user in message.mentions:
                if mentioned_user.id in self.afk_data:
                    reason = self.afk_data[mentioned_user.id]
                    await message.channel.send(f"💤 **{mentioned_user.name}** is AFK: {reason}", delete_after=10)

async def setup(bot):
    # This must match the class name "General"
    await bot.add_cog(General(bot))
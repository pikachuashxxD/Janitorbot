import discord
import os
import asyncio
from discord.ext import commands
import config

# --- SETUP ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- LOAD COGS ---
async def load_extensions():
    # Looks for files ending in .py inside the 'cogs' folder
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != "__init__.py":
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Loaded Extension: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    print("--------------------------------")
    print(f"🚀 Logged in as {bot.user.name}")
    print(f"🆔 ID: {bot.user.id}")
    print("--------------------------------")
    try:
        synced = await bot.tree.sync()
        print(f"🌍 Synced {len(synced)} Slash Commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(config.TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
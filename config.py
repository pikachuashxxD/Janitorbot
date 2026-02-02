import os
from dotenv import load_dotenv

load_dotenv()

# --- SECRETS ---
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 123456789012345678  # Replace with YOUR User ID (for debugging)

# --- VISUALS ---
EMOJIS = {
    "trash": "🗑️",
    "edit": "✏️",
    "voice_join": "🟢",
    "voice_leave": "🔴",
    "voice_move": "🔄",
    "sparkles": "✨",
    "loading": "⏳",
    "welcome": "👋"
}

# --- COLORS ---
COLOR_RED = 0xff0000
COLOR_GREEN = 0x00ff00
COLOR_BLUE = 0x0000ff
COLOR_GOLD = 0xffd700
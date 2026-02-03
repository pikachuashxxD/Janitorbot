import os
from dotenv import load_dotenv

load_dotenv()

# --- SECRETS ---
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 123456789012345678  # Replace with YOUR User ID (for debugging)

# --- VISUALS ---
EMOJIS = {
    # --- Static Emojis (Backups) ---
    "trash": "🗑️",
    "edit": "📝",
    "voice_join": "🟢",
    "voice_leave": "🔴",
    "voice_move": "🔄",
    "sparkles": "✨",
    "loading": "⏳",
    "welcome": "👋",
    "hammer": "🔨",
    "boot": "👢",
    "timeout": "⏳",

    # --- Animated Emojis (Paste your IDs here!) ---
    # Example format: "<a:emoji_name:1234567890>"
    "anim_delete": "🗑️",     # Replace with animated trash can
    "anim_edit": "📝",       # Replace with animated pencil
    "anim_join": "🟢",       # Replace with animated green circle/enter
    "anim_leave": "🔴",      # Replace with animated red circle/exit
    "anim_move": "🔄",       # Replace with animated swap/move icon
    "anim_alert": "🚨"       # Replace with animated alert siren
}
# --- COLORS ---
COLOR_RED = 0xff0000
COLOR_GREEN = 0x00ff00
COLOR_BLUE = 0x0000ff
COLOR_GOLD = 0xffd700
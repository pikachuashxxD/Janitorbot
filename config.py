import os
from dotenv import load_dotenv

load_dotenv()

# --- SECRETS ---
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 746366595458138183
BOT_LOG_CHANNEL = 1468368359761645640  # Replace with YOUR User ID (for debugging)

# --- VISUALS ---
EMOJIS = {
    "trash": "<a:anim_trash:1468227963790033121>",   # Replace with your Trash ID
    "edit": "<a:anim_edit:1468219480067805301>",     # Replace with your Edit/Pencil ID
    "voice_join": "<a:anim_join:1468219262819631113>", # Replace with Green Join ID
    "voice_leave": "<a:anim_leave:1468229979556020285>", # Replace with Red Leave ID
    "voice_move": "<a:anim_move:1468222918319280256>", # Replace with Move/Swap ID
    
    # Static Fallbacks (Keep these just in case)
    "timeout": "⏳",
    "boot": "👢",
    "sparkles": "✨",
    "loading": "⏳",
    "welcome": "👋"
}
# --- COLORS ---
COLOR_RED = 0xff0000
COLOR_GREEN = 0x00ff00
COLOR_BLUE = 0x0000ff
COLOR_GOLD = 0xffd700
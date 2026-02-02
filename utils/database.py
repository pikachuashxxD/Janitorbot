import json
import os

# Define path
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "server_configs.json")

# Ensure directory and file exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def get_config(guild_id):
    """Fetch configuration for a specific server."""
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data.get(str(guild_id), {})

def update_config(guild_id, key, value):
    """Update a specific setting for a server."""
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    
    guild_id = str(guild_id)
    if guild_id not in data:
        data[guild_id] = {}
    
    data[guild_id][key] = value
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
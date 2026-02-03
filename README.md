# 🧹 Janitorbot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0%2B-5865F2?style=for-the-badge&logo=discord)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Janitorbot** is a specialized Discord utility bot featuring a fully automated **Clan System**, **Streamer Alerts**, **Moderation**, and advanced **Owner Logging**. It allows communities to self-manage clans with Leaders, Applications, and Private Channels.

---

## ✨ Key Features

### 🛡️ Clan System (`cogs/clans.py`)
* **Create & Manage:** Users can request to create clans (Admin approved).
* **Automated Permissions:** Creates a private Category, Text Channel, and Role for each clan.
* **Membership Logic:** Leaders can **Kick** members and **Transfer Ownership**.
* **Global Leaderboard:** `/clan_list` displays the top clans across **all servers**, showing the Clan Name, Leader, Member Count, and **Server of Origin**.

### 👑 Owner & Admin Tools (`cogs/owner.py`)
* **System Logging:** Dedicated logs for Bot Errors, Guild Joins/Leaves, and Database Backups.
* **Database Backup:** `/owner backup` instantly uploads a copy of the database (`clans.json`) to Discord.
* **Status Control:** Change the bot's status (Playing, Streaming, Listening) instantly.

### 🛠️ Moderation & Setup (`cogs/moderation.py`, `cogs/setup.py`)
* **Logging:** Track deleted messages, edited messages, voice activity, and member joins (`cogs/logging.py`).
* **Welcome System:** Customizable welcome images and messages (`cogs/welcome.py`).
* **Streamer Alerts:** Auto-assign roles and post when users go live (`cogs/streming.py`).

### 🎮 Utilities (`cogs/general.py`)
* **Team Splitter:** `/teams` to balance players for custom games.
* **AFK System:** Auto-responses when a user is mentioned while AFK.

---

## 📂 Project Structure

```text
├── cogs/
│   ├── clans.py       # Core Clan System (Creation, Management, Leaderboard)
│   ├── general.py     # AFK, Teams, and Utilities
│   ├── help.py        # Dynamic Dropdown Help Menu
│   ├── logging.py     # Message & Voice Logger
│   ├── moderation.py  # Kick, Ban, Mute commands
│   ├── owner.py       # Owner-only commands & Backups
│   ├── setup.py       # Configuration commands
│   ├── streming.py    # Streamer Alerts logic
│   └── welcome.py     # Welcome Image generator
├── utils/
│   └── database.py    # JSON handling logic
├── .env               # Environment Secrets (Token)
├── config.py          # Configuration settings
├── main.py            # Bot Entry Point
├── requirements.txt   # Python Dependencies
└── README.md          # Documentation
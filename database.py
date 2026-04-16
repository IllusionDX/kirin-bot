import sqlite3
import os
from pathlib import Path

IS_PRODUCTION = os.environ.get("FLY_APP_NAME") is not None

if IS_PRODUCTION:
    DB_PATH = Path("/data") / "kirin.db"
else:
    DB_PATH = Path("kirin.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, language TEXT DEFAULT 'en')")
conn.commit()

def get_language(guild_id: int) -> str:
    cursor = conn.execute("SELECT language FROM guild_settings WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    return row[0] if row else "en"

def set_language(guild_id: int, language: str):
    conn.execute("INSERT OR REPLACE INTO guild_settings (guild_id, language) VALUES (?, ?)", (guild_id, language))
    conn.commit()
import os
from dotenv import load_dotenv

# если локально — загрузит .env
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "").split(",")))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
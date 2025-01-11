import os

from telegram import Bot

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Срок действия Access Token
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Срок действия Refresh Token

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

import os

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Срок действия Access Token
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Срок действия Refresh Token
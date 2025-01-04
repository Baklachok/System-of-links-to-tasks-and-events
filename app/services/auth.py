from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from passlib.context import CryptContext

from app.core.db import get_db
from app.core.logger import logger
from app.models.user import User
from app.schemas.auth import UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # URL для получения токена


def hash_password(password: str) -> str:
    logger.info("Хэширование пароля")
    hashed = pwd_context.hash(password)
    logger.debug(f"Хэшированный пароль: {hashed}")
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info("Проверка пароля")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"Результат проверки пароля: {result}")
    return result


def create_access_token(data: dict) -> str:
    logger.info("Создание access-токена")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Access-токен создан: {token}")
    return token


def create_refresh_token(data: dict) -> str:
    logger.info("Создание refresh-токена")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Refresh-токен создан: {token}")
    return token


def decode_token(token: str) -> Optional[dict]:
    logger.info("Декодирование токена")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Декодированный payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Попытка использовать истёкший токен")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        logger.error("Ошибка декодирования токена")
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> UserResponse:
    # Сначала пытаемся взять токен из куки
    token = request.cookies.get("access_token")
    if not token:
        # Если токен отсутствует в куки, проверяем заголовок Authorization
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ", 1)[1]
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Декодируем токен
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Ищем пользователя в базе
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return UserResponse(id=user.id, email=user.email, is_active=user.is_active)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

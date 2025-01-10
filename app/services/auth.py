from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.core.db import get_db
from app.core.logger import logger
from app.models.user import User
from app.schemas.auth import UserResponse

# Настройка контекста для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# URL для получения токена в FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Хэширует пароль с использованием Passlib (bcrypt).

    :param password: Обычный текст пароля.
    :return: Хэшированный пароль.
    """
    logger.info("Хэширование пароля")
    hashed = pwd_context.hash(password)
    logger.debug(f"Хэшированный пароль: {hashed}")
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет пароль на совпадение с хэшированным значением.

    :param plain_password: Обычный текст пароля.
    :param hashed_password: Хэшированный пароль.
    :return: True, если пароли совпадают, иначе False.
    """
    logger.info("Проверка пароля")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"Результат проверки пароля: {result}")
    return result


def create_access_token(data: dict) -> str:
    """
    Создаёт access-токен с истечением времени.

    :param data: Данные для кодирования в токен.
    :return: JWT access-токен.
    """
    logger.info("Создание access-токена")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug("Access-токен создан")
    return token


def create_refresh_token(data: dict) -> str:
    """
    Создаёт refresh-токен с истечением времени.

    :param data: Данные для кодирования в токен.
    :return: JWT refresh-токен.
    """
    logger.info("Создание refresh-токена")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug("Refresh-токен создан")
    return token


def decode_token(token: str) -> dict:
    """
    Декодирует токен и возвращает payload.

    :param token: JWT токен.
    :return: Расшифрованные данные токена.
    :raises HTTPException: Если токен истёк или недействителен.
    """
    logger.info("Декодирование токена")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Декодированный payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Попытка использовать истёкший токен")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        logger.error(f"Ошибка декодирования токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Получает текущего пользователя из токена.

    :param request: HTTP запрос.
    :param db: Сессия базы данных.
    :return: Схема пользователя UserResponse.
    :raises HTTPException: Если токен или пользователь недействителен.
    """
    logger.info("Получение текущего пользователя")

    # Проверка токена в куках или заголовке Authorization
    token = request.cookies.get("access_token") or _extract_token_from_header(request)

    # Декодируем токен и извлекаем идентификатор пользователя
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Поле 'sub' отсутствует в токене")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Поиск пользователя в базе данных
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("Пользователь с указанным ID не найден")
        raise HTTPException(status_code=401, detail="User not found")

    logger.debug(f"Пользователь найден: {user.email}")
    return UserResponse(id=user.id, email=user.email, is_active=user.is_active, telegram_chat_id=user.telegram_chat_id)


def _extract_token_from_header(request: Request) -> str:
    """
    Извлекает токен из заголовка Authorization.

    :param request: HTTP запрос.
    :return: JWT токен.
    :raises HTTPException: Если токен отсутствует или имеет неверный формат.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Токен отсутствует в заголовке Authorization")
        raise HTTPException(status_code=401, detail="Not authenticated")
    return auth_header.split(" ", 1)[1]


def save_telegram_chat_id(db: Session, user_id: str, chat_id: str) -> None:
    """
    Сохраняет Telegram Chat ID для пользователя.

    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :param chat_id: Telegram Chat ID.
    :raises ValueError: Если пользователь не найден.
    """
    logger.info(f"Сохранение Telegram Chat ID для пользователя ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.error(f"Пользователь с ID {user_id} не найден")
        raise ValueError(f"Пользователь с ID {user_id} не найден.")

    user.telegram_chat_id = chat_id
    db.commit()
    logger.info(f"Telegram Chat ID успешно сохранён для пользователя ID: {user_id}")

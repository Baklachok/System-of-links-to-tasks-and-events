from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.db import get_db
from app.logger import logger
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from app.services.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)

router = APIRouter()


def get_user_by_id(user_id: str, db: Session) -> User:
    """Получить пользователя по ID из базы данных."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"Пользователь с ID {user_id} не найден")
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_by_email(email: str, db: Session) -> User:
    """Получить пользователя по email из базы данных."""
    return db.query(User).filter(User.email == email).first()


def validate_access_token(request: Request) -> dict:
    """Извлечь и декодировать токен доступа."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.warning("Токен доступа отсутствует")
        raise HTTPException(status_code=401, detail="Access token missing")
    logger.info(f"Токен: {access_token}")
    try:
        return decode_token(access_token)
    except Exception as e:
        logger.error(f"Ошибка декодирования токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid access token")


@router.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя."""
    if get_user_by_email(user.email, db):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(id=str(uuid4()), email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Зарегистрирован новый пользователь: {user.email}")
    return new_user


@router.post("/auth/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Авторизация пользователя и установка токенов."""
    db_user = get_user_by_email(user.email, db)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logger.warning(f"Неудачная попытка входа для {user.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Генерация токенов
    access_token = create_access_token(data={"sub": db_user.id})
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    # Установка токенов в куки
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS
    )
    logger.info(f"Успешный вход для пользователя {user.email}")
    return {"message": "Login successful"}


@router.post("/auth/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Обновление токена доступа."""
    refresh_token = request.cookies.get("refresh_token")
    logger.debug(f"refresh_token - {refresh_token}")
    if not refresh_token:
        logger.warning("Refresh токен отсутствует")
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = decode_token(refresh_token)
    except Exception as e:
        logger.error(f"Ошибка декодирования refresh токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("ID пользователя отсутствует в refresh токене")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    get_user_by_id(user_id, db)  # Проверка существования пользователя

    # Генерация нового Access Token
    new_access_token = create_access_token(data={"sub": user_id})
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True, max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES
    )
    logger.info(f"Access токен обновлен для пользователя {user_id}")
    return {"message": "Token refreshed"}


@router.get("/auth/me", response_model=UserResponse)
def get_me(request: Request, db: Session = Depends(get_db)):
    """Получение данных текущего пользователя."""
    logger.info("Получен запрос на /auth/me")
    payload = validate_access_token(request)
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("ID пользователя отсутствует в токене")
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = get_user_by_id(user_id, db)
    logger.info(f"Пользователь найден: {user.email}")
    return user

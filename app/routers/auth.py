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


@router.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = User(id=str(uuid4()), email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/auth/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
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
    return {"message": "Login successful"}


@router.post("/auth/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = decode_token(refresh_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Генерация нового Access Token
    new_access_token = create_access_token(data={"sub": user_id})
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True, max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return {"message": "Token refreshed"}


@router.get("/auth/me", response_model=UserResponse)
def get_me(request: Request, db: Session = Depends(get_db)):
    logger.info("Получен запрос на /auth/me")

    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.warning("Токен доступа отсутствует")
        raise HTTPException(status_code=401, detail="Access token missing")

    logger.info(f"Токен: {access_token}")
    try:
        payload = decode_token(access_token)
    except Exception as e:
        logger.error(f"Ошибка декодирования токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid access token")

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("ID пользователя отсутствует в токене")
        raise HTTPException(status_code=401, detail="Invalid access token")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        logger.warning(f"Пользователь с ID {user_id} не найден")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"Пользователь найден: {db_user.email}")
    return db_user

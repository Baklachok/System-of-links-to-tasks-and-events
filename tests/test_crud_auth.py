import jwt
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from app.core.config import SECRET_KEY, ALGORITHM
from app.core.db import Base
from app.main import app
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User

# Конфигурация тестовой базы данных
TEST_DATABASE_URL = "sqlite:///./test.db"  # SQLite для тестов
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Тестовые данные
TEST_USER_ID = "test-user-id"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"
TEST_HASHED_PASSWORD = hash_password(TEST_PASSWORD)


# ---- Фикстуры ----

@pytest.fixture(scope="function")
def db():
    """Фикстура для тестовой базы данных."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Фикстура для тестового клиента FastAPI."""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Создаёт тестового пользователя в базе данных."""
    user = User(
        id=TEST_USER_ID,
        email=TEST_EMAIL,
        hashed_password=TEST_HASHED_PASSWORD,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def access_token():
    """Генерирует тестовый access-токен."""
    data = {"sub": TEST_USER_ID}
    return create_access_token(data)


@pytest.fixture
def refresh_token():
    """Генерирует тестовый refresh-токен."""
    data = {"sub": TEST_USER_ID}
    return create_refresh_token(data)


@pytest.fixture
def client_with_cookies(client, access_token):
    """Клиент с установленным токеном в cookies."""
    client.cookies.set("access_token", access_token)
    return client


# ---- Тесты функций ----

def test_hash_password():
    """Тест хэширования пароля."""
    hashed = hash_password(TEST_PASSWORD)
    assert hashed != TEST_PASSWORD, "Хэшированный пароль не должен совпадать с исходным"
    assert len(hashed) > 0, "Хэшированный пароль не должен быть пустым"


def test_verify_password():
    """Тест проверки пароля."""
    assert verify_password(TEST_PASSWORD, TEST_HASHED_PASSWORD) is True
    assert verify_password("wrongpassword", TEST_HASHED_PASSWORD) is False


def test_create_access_token():
    """Тест создания access-токена."""
    data = {"sub": TEST_USER_ID}
    token = create_access_token(data)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == TEST_USER_ID
    assert "exp" in payload, "Токен должен содержать поле exp"
    assert datetime.utcfromtimestamp(payload["exp"]) > datetime.utcnow()


def test_create_refresh_token():
    """Тест создания refresh-токена."""
    data = {"sub": TEST_USER_ID}
    token = create_refresh_token(data)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == TEST_USER_ID
    assert "exp" in payload
    assert datetime.utcfromtimestamp(payload["exp"]) > datetime.utcnow()


def test_decode_token(access_token):
    """Тест декодирования корректного токена."""
    payload = decode_token(access_token)
    assert payload["sub"] == TEST_USER_ID


def test_decode_token_expired():
    """Тест обработки истёкшего токена."""
    expired_token = jwt.encode(
        {"sub": TEST_USER_ID, "exp": datetime.utcnow() - timedelta(seconds=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(Exception, match="Token has expired"):
        decode_token(expired_token)


def test_decode_token_invalid():
    """Тест обработки некорректного токена."""
    with pytest.raises(Exception, match="Invalid token"):
        decode_token("invalid.token")


# ---- Тесты конечных точек ----

def test_get_current_user(client_with_cookies, test_user):
    """Тест получения текущего пользователя с валидным токеном."""
    response = client_with_cookies.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_current_user_no_token(client):
    """Тест получения текущего пользователя без токена."""
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token missing"


def test_get_current_user_invalid_token(client):
    """Тест получения текущего пользователя с некорректным токеном."""
    client.cookies.set("access_token", "invalid.token")
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"

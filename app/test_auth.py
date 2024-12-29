import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db
from app.models.user import User
from app.services.auth import hash_password

# Настройка тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Тестовый клиент
client = TestClient(app)


# Фикстуры
@pytest.fixture(scope="function")
def db_session():
    """Создание и удаление тестовой базы данных для каждого теста."""
    Base.metadata.create_all(bind=engine)  # Создаём таблицы
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Удаляем таблицы после тестов


@pytest.fixture(scope="function", autouse=True)
def override_get_db(db_session):
    """Переопределение зависимости get_db для использования тестовой базы данных."""
    app.dependency_overrides[get_db] = lambda: db_session


@pytest.fixture
def create_test_user(db_session):
    """Создаёт тестового пользователя в базе данных."""
    def _create_user(email="test@example.com", password="password123", user_id="test-id"):
        user = User(id=user_id, email=email, hashed_password=hash_password(password))
        db_session.add(user)
        db_session.commit()
        return user
    return _create_user


# Вспомогательные функции
def login_user(email="test@example.com", password="password123"):
    """Логинит пользователя и возвращает токены."""
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {
        "access_token": response.cookies.get("access_token"),
        "refresh_token": response.cookies.get("refresh_token")
    }


# Тесты
def test_register(db_session):
    """Тест успешной регистрации пользователя."""
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_register_existing_email(create_test_user):
    """Тест регистрации с уже существующим email."""
    create_test_user()
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


def test_login_success(create_test_user):
    """Тест успешного входа пользователя."""
    create_test_user()
    response = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_invalid_credentials():
    """Тест входа с неверными данными."""
    response = client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_refresh_token(create_test_user):
    """Тест обновления токена доступа."""
    create_test_user()
    tokens = login_user()

    response = client.post("/auth/refresh", cookies={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    assert response.json() == {"message": "Token refreshed"}
    assert "access_token" in response.cookies


def test_refresh_token_missing():
    """Тест обновления токена при отсутствии refresh токена."""
    client.cookies.clear()
    response = client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh token missing"}


def test_get_me(create_test_user):
    """Тест получения данных текущего пользователя."""
    create_test_user()
    tokens = login_user()

    response = client.get("/auth/me", cookies={"access_token": tokens["access_token"]})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_get_me_unauthorized():
    """Тест получения данных текущего пользователя без авторизации."""
    client.cookies.clear()
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Access token missing"}

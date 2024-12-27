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


# Создаём фикстуру для тестовой базы данных
@pytest.fixture(scope="function")
def db_session():
    """Фикстура для создания базы данных."""
    Base.metadata.create_all(bind=engine)  # Создаём таблицы
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Удаляем таблицы после тестов


# Переопределяем зависимость get_db
@pytest.fixture(scope="function", autouse=True)
def override_get_db(db_session):
    app.dependency_overrides[get_db] = lambda: db_session


# Тесты
def test_register(db_session):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_register_existing_email(db_session):
    db_session.add(User(
        id="test-id",
        email="test@example.com",
        hashed_password=hash_password("password123")
    ))
    db_session.commit()

    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


def test_login_success(db_session):
    db_session.add(User(
        id="test-id",
        email="test@example.com",
        hashed_password=hash_password("password123")
    ))
    db_session.commit()

    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_invalid_credentials():
    response = client.post("/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_refresh_token(db_session):
    db_session.add(User(
        id="test-id",
        email="test@example.com",
        hashed_password=hash_password("password123")
    ))
    db_session.commit()

    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    refresh_token = login_response.cookies.get("refresh_token")

    response = client.post("/auth/refresh", cookies={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json() == {"message": "Token refreshed"}
    assert "access_token" in response.cookies


def test_get_me(db_session):
    db_session.add(User(
        id="test-id",
        email="test@example.com",
        hashed_password=hash_password("password123")
    ))
    db_session.commit()

    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    access_token = login_response.cookies.get("access_token")

    response = client.get("/auth/me", cookies={"access_token": access_token})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_get_me_unauthorized():
    client.cookies.clear()
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Access token missing"}

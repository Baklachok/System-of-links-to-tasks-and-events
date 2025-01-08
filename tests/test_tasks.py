import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.logger import logger
from app.main import app
from app.core.db import Base, get_db
from app.models.user import User
from app.services.auth import hash_password, create_access_token

# Тестовая база данных SQLite (in-memory)
TEST_DATABASE_URL = "sqlite:///./test.db"

# Настройка тестового движка и сессии
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Инициализация тестовой базы данных."""
    logger.info("Инициализация тестовой базы данных")
    Base.metadata.create_all(bind=engine)  # Создание схемы
    connection = engine.connect()         # Явное создание соединения
    transaction = connection.begin()      # Начало транзакции

    db = TestingSessionLocal(bind=connection)
    try:
        yield db
    finally:
        logger.info("Откат изменений и удаление схемы базы данных")
        db.close()                        # Закрытие сессии
        transaction.rollback()            # Откат транзакции
        connection.close()                # Закрытие соединения
        Base.metadata.drop_all(bind=engine)  # Удаление схемы


@pytest.fixture
def override_get_db(db):
    """Переопределение зависимости базы данных для тестов."""
    logger.info("Переопределение зависимости get_db для тестов")
    app.dependency_overrides[get_db] = lambda: db
    yield
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app)


@pytest.fixture
def test_user(db):
    """Создание тестового пользователя."""
    logger.info("Создание тестового пользователя")
    user = User(
        id="test-user-id",
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.debug(f"Тестовый пользователь создан: {user}")
    return user


@pytest.fixture
def auth_headers(test_user):
    """Создание заголовков авторизации."""
    logger.info("Создание заголовков авторизации")
    access_token = create_access_token({"sub": test_user.id})
    headers = {"Authorization": f"Bearer {access_token}"}
    logger.debug(f"Заголовки авторизации: {headers}")
    return headers


@pytest.fixture
def task_data(test_user):
    """Тестовые данные для задачи."""
    logger.info("Создание тестовых данных для задачи")
    data = {
        "title": "Test Task",
        "description": "Test Description",
        "completed": False,
        "user_id": test_user.id,
    }
    logger.debug(f"Тестовые данные для задачи: {data}")
    return data


@pytest.fixture
def updated_task_data():
    """Тестовые данные для обновленной задачи."""
    logger.info("Создание данных для обновленной задачи")
    data = {
        "title": "Updated Task",
        "description": "Updated Description",
        "completed": True,
    }
    logger.debug(f"Обновленные данные задачи: {data}")
    return data


# Тесты
@pytest.mark.usefixtures("override_get_db")
def test_create_task(db, task_data, auth_headers):
    """Тест: создание новой задачи."""
    logger.info("Тест: создание новой задачи")
    response = client.post("/tasks", json=task_data, headers=auth_headers)
    logger.debug(f"Ответ сервера: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["completed"] == task_data["completed"]


@pytest.mark.usefixtures("override_get_db")
def test_list_tasks(db, task_data, auth_headers):
    """Тест: получение списка задач."""
    logger.info("Тест: получение списка задач")
    client.post("/tasks", json=task_data, headers=auth_headers)

    response = client.get("/tasks", headers=auth_headers)
    logger.debug(f"Ответ сервера: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == task_data["title"]


@pytest.mark.usefixtures("override_get_db")
def test_get_task(db, task_data, auth_headers):
    """Тест: получение задачи по ID."""
    logger.info("Тест: получение задачи по ID")
    response = client.post("/tasks", json=task_data, headers=auth_headers)
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    logger.debug(f"Ответ сервера: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == task_data["title"]


@pytest.mark.usefixtures("override_get_db")
def test_update_task(db, task_data, updated_task_data, auth_headers):
    """Тест: обновление задачи."""
    logger.info("Тест: обновление задачи")
    response = client.post("/tasks", json=task_data, headers=auth_headers)
    task_id = response.json()["id"]

    response = client.put(f"/tasks/{task_id}", json=updated_task_data, headers=auth_headers)
    logger.debug(f"Ответ сервера: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == updated_task_data["title"]
    assert data["description"] == updated_task_data["description"]
    assert data["completed"] == updated_task_data["completed"]


@pytest.mark.usefixtures("override_get_db")
def test_delete_task(db, task_data, auth_headers):
    """Тест: удаление задачи."""
    logger.info("Тест: удаление задачи")
    response = client.post("/tasks", json=task_data, headers=auth_headers)
    task_id = response.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    logger.debug(f"Ответ сервера при удалении: {response.status_code}")
    assert response.status_code == 204
    assert response.content == b""

    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    logger.debug(f"Ответ сервера при повторном запросе удаленной задачи: {response.status_code}")
    assert response.status_code == 404

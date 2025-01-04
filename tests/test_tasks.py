import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import Base, get_db

# Настройка тестовой базы данных
TEST_DATABASE_URL = "sqlite:///./test.db"  # SQLite для тестов

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаём тестовую сессию базы данных
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Переопределяем зависимость для тестов
app.dependency_overrides[get_db] = lambda: next(db())

# Создаём клиент для тестирования
client = TestClient(app)

# Фикстуры для тестовых данных
@pytest.fixture
def task_data():
    return {"title": "Test Task", "description": "Test Description", "completed": False}

@pytest.fixture
def updated_task_data():
    return {"title": "Updated Task", "description": "Updated Description", "completed": True}


# Тесты
def test_create_task(db, task_data):
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["completed"] == task_data["completed"]


def test_list_tasks(db, task_data):
    # Создаём тестовую задачу
    client.post("/tasks", json=task_data)

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == task_data["title"]


def test_get_task(db, task_data):
    # Создаём задачу
    response = client.post("/tasks", json=task_data)
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == task_data["title"]


def test_update_task(db, task_data, updated_task_data):
    # Создаём задачу
    response = client.post("/tasks", json=task_data)
    task_id = response.json()["id"]

    # Обновляем задачу
    response = client.put(f"/tasks/{task_id}", json=updated_task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == updated_task_data["title"]
    assert data["description"] == updated_task_data["description"]
    assert data["completed"] == updated_task_data["completed"]


def test_delete_task(db, task_data):
    # Создаём задачу
    response = client.post("/tasks", json=task_data)
    task_id = response.json()["id"]

    # Удаляем задачу
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Task deleted successfully"}

    # Проверяем, что задача удалена
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404

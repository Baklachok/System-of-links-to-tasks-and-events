import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate
from app.services.tasks import get_tasks_by_user_id, create_task_for_user, get_task_by_id_and_user, update_task_by_id, \
    delete_task_by_id

DATABASE_URL = "sqlite:///:memory:"  # SQLite в памяти

@pytest.fixture(scope="module")
def test_db():
    """Создаёт тестовую базу данных в памяти."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    """Фиктивный пользователь для тестов."""
    return {"id": "test_user_id"}

@pytest.fixture(autouse=True)
def clean_db(test_db):
    """Очищает базу данных перед каждым тестом."""
    try:
        with test_db.begin_nested():  # Явная транзакция
            for table in reversed(Base.metadata.sorted_tables):
                test_db.execute(table.delete())
        test_db.commit()
    except Exception as e:
        test_db.rollback()
        raise RuntimeError(f"Ошибка очистки базы данных: {e}")


def test_get_tasks_by_user_id(test_db, test_user):
    # Добавляем фиктивные задачи
    test_db.add(Task(title="Task 1", user_id=test_user["id"]))
    test_db.add(Task(title="Task 2", user_id="another_user_id"))
    test_db.commit()

    # Получаем задачи для test_user
    tasks = get_tasks_by_user_id(test_db, test_user["id"])
    assert len(tasks) == 1
    assert tasks[0].title == "Task 1"


def test_create_task_for_user(test_db, test_user):
    task_data = TaskCreate(title="New Task", description="Test description")
    task = create_task_for_user(test_db, task_data, test_user["id"])

    assert task.title == "New Task"
    assert task.description == "Test description"
    assert task.user_id == test_user["id"]

    # Убедимся, что задача сохранилась в базе данных
    tasks = test_db.query(Task).filter(Task.user_id == test_user["id"]).all()
    assert len(tasks) == 1
    assert tasks[0].title == "New Task"


def test_get_task_by_id_and_user(test_db, test_user):
    # Добавляем фиктивную задачу
    task = Task(title="Test Task", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    # Получаем задачу по ID
    fetched_task = get_task_by_id_and_user(test_db, task.id, test_user["id"])
    assert fetched_task is not None
    assert fetched_task.title == "Test Task"

    # Проверяем доступ к задаче другого пользователя
    fetched_task = get_task_by_id_and_user(test_db, task.id, "another_user_id")
    assert fetched_task is None


def test_update_task_by_id(test_db, test_user):
    # Добавляем фиктивную задачу
    task = Task(title="Old Task", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    # Обновляем задачу
    updated_task = update_task_by_id(
        test_db, task.id, TaskUpdate(title="Updated Task"), test_user["id"]
    )
    assert updated_task.title == "Updated Task"

    # Убедимся, что изменения сохранены
    db_task = test_db.query(Task).filter(Task.id == task.id).first()
    assert db_task.title == "Updated Task"


def test_delete_task_by_id(test_db, test_user):
    # Добавляем фиктивную задачу
    task = Task(title="Task to delete", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    # Удаляем задачу
    success = delete_task_by_id(test_db, task.id, test_user["id"])
    assert success is True

    # Убедимся, что задача удалена
    db_task = test_db.query(Task).filter(Task.id == task.id).first()
    assert db_task is None

    # Попробуем удалить несуществующую задачу
    success = delete_task_by_id(test_db, task.id, test_user["id"])
    assert success is False

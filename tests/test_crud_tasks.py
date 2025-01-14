import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.core.logger import logger
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate
from app.services.tasks import (
    get_tasks_by_user_id,
    create_task_for_user,
    get_task_by_id_and_user,
    update_task_by_id,
    delete_task_by_id, get_tasks_with_email_notifications, get_tasks_with_telegram_notifications,
    get_tasks_with_sms_notifications,
)

DATABASE_URL = "sqlite:///:memory:"  # SQLite в памяти


@pytest.fixture(scope="module")
def test_engine():
    """Создаёт тестовый движок базы данных."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Создаёт тестовую сессию базы данных."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def test_user():
    """Возвращает фиктивного пользователя для тестов."""
    return {"id": "test_user_id"}


@pytest.fixture(autouse=True)
def clean_db(test_db):
    """Очищает базу данных перед каждым тестом."""
    try:
        with test_db.begin_nested():  # Явная транзакция для отката изменений после теста
            for table in reversed(Base.metadata.sorted_tables):
                test_db.execute(table.delete())
        test_db.commit()
    except Exception as e:
        test_db.rollback()
        logger.error(f"Ошибка очистки базы данных: {e}")
        raise RuntimeError(f"Ошибка очистки базы данных: {e}")


# --------------------- Тесты ---------------------

def test_get_tasks_by_user_id(test_db, test_user):
    """Тест: получение задач по ID пользователя."""
    test_db.add(Task(title="Task 1", user_id=test_user["id"]))
    test_db.add(Task(title="Task 2", user_id="another_user_id"))
    test_db.commit()

    tasks = get_tasks_by_user_id(test_db, test_user["id"])

    assert len(tasks) == 1
    assert tasks[0].title == "Task 1"


def test_create_task_for_user(test_db, test_user):
    """Тест: создание задачи для пользователя."""
    task_data = TaskCreate(title="New Task", description="Test description")
    task = create_task_for_user(test_db, task_data, test_user["id"])

    assert task.title == "New Task"
    assert task.description == "Test description"
    assert task.user_id == test_user["id"]

    tasks = test_db.query(Task).filter(Task.user_id == test_user["id"]).all()
    assert len(tasks) == 1
    assert tasks[0].title == "New Task"


def test_get_task_by_id_and_user(test_db, test_user):
    """Тест: получение задачи по ID и ID пользователя."""
    task = Task(title="Test Task", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    fetched_task = get_task_by_id_and_user(test_db, task.id, test_user["id"])
    assert fetched_task is not None
    assert fetched_task.title == "Test Task"

    fetched_task = get_task_by_id_and_user(test_db, task.id, "another_user_id")
    assert fetched_task is None


def test_update_task_by_id(test_db, test_user):
    """Тест: обновление задачи по ID."""
    task = Task(title="Old Task", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    updated_task = update_task_by_id(
        test_db, task.id, TaskUpdate(title="Updated Task"), test_user["id"]
    )

    assert updated_task.title == "Updated Task"

    db_task = test_db.query(Task).filter(Task.id == task.id).first()
    assert db_task.title == "Updated Task"


def test_delete_task_by_id(test_db, test_user):
    """Тест: удаление задачи по ID."""
    task = Task(title="Task to delete", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    success = delete_task_by_id(test_db, task.id, test_user["id"])
    assert success is True

    db_task = test_db.query(Task).filter(Task.id == task.id).first()
    assert db_task is None

    success = delete_task_by_id(test_db, task.id, test_user["id"])
    assert success is False


def test_get_tasks_by_user_id_no_tasks(test_db, test_user):
    """Тест: получение задач по ID пользователя, когда задач нет."""
    tasks = get_tasks_by_user_id(test_db, test_user["id"])
    assert len(tasks) == 0


def test_create_task_with_empty_fields(test_db, test_user):
    """Тест: создание задачи с минимальным набором полей."""
    task_data = TaskCreate(title="Minimal Task")
    task = create_task_for_user(test_db, task_data, test_user["id"])

    assert task.title == "Minimal Task"
    assert task.description is None  # Проверяем, что поле description необязательно
    assert task.user_id == test_user["id"]


def test_get_task_by_invalid_id(test_db, test_user):
    """Тест: попытка получить задачу с несуществующим ID."""
    task = get_task_by_id_and_user(test_db, task_id=999, user_id=test_user["id"])
    assert task is None


def test_update_task_with_partial_data(test_db, test_user):
    """Тест: частичное обновление задачи."""
    task = Task(title="Original Task", description="Original Description", user_id=test_user["id"])
    test_db.add(task)
    test_db.commit()

    updated_task = update_task_by_id(
        test_db, task.id, TaskUpdate(description="Updated Description"), test_user["id"]
    )

    assert updated_task.title == "Original Task"  # Убедимся, что поле title не изменилось
    assert updated_task.description == "Updated Description"


def test_update_task_not_found(test_db, test_user):
    """Тест: обновление задачи с несуществующим ID."""
    updated_task = update_task_by_id(
        test_db, task_id=999, task_data=TaskUpdate(title="New Title"), user_id=test_user["id"]
    )
    assert updated_task is None


def test_delete_task_not_found(test_db, test_user):
    """Тест: удаление задачи с несуществующим ID."""
    success = delete_task_by_id(test_db, task_id=999, user_id=test_user["id"])
    assert success is False


def test_get_tasks_with_email_notifications(test_db, test_user):
    """Тест: получение задач с email-уведомлениями."""
    task_with_email = Task(
        title="Email Task", user_id=test_user["id"], email_notification=True, completed=False
    )
    task_completed = Task(
        title="Completed Task", user_id=test_user["id"], email_notification=True, completed=True
    )
    test_db.add(task_with_email)
    test_db.add(task_completed)
    test_db.commit()

    tasks = get_tasks_with_email_notifications(test_db)
    assert len(tasks) == 1
    assert tasks[0].title == "Email Task"


def test_get_tasks_with_telegram_notifications(test_db, test_user):
    """Тест: получение задач с Telegram-уведомлениями."""
    task_with_telegram = Task(
        title="Telegram Task", user_id=test_user["id"], telegram_notification=True, completed=False
    )
    task_without_telegram = Task(
        title="No Telegram Task", user_id=test_user["id"], telegram_notification=False, completed=False
    )
    test_db.add(task_with_telegram)
    test_db.add(task_without_telegram)
    test_db.commit()

    tasks = get_tasks_with_telegram_notifications(test_db)
    assert len(tasks) == 1
    assert tasks[0].title == "Telegram Task"


def test_get_tasks_with_sms_notifications(test_db, test_user):
    """Тест: получение задач с SMS-уведомлениями."""
    task_with_sms = Task(
        title="SMS Task", user_id=test_user["id"], sms_notification=True, completed=False
    )
    task_completed = Task(
        title="Completed SMS Task", user_id=test_user["id"], sms_notification=True, completed=True
    )
    test_db.add(task_with_sms)
    test_db.add(task_completed)
    test_db.commit()

    tasks = get_tasks_with_sms_notifications(test_db)
    assert len(tasks) == 1
    assert tasks[0].title == "SMS Task"


def test_create_task_for_user_with_long_title(test_db, test_user):
    """Тест: создание задачи с очень длинным названием."""
    long_title = "A" * 256  # Заголовок длиной 256 символов
    task_data = TaskCreate(title=long_title, description="Test description")
    task = create_task_for_user(test_db, task_data, test_user["id"])

    assert len(task.title) == 256
    assert task.title == long_title


def test_delete_task_by_another_user(test_db, test_user):
    """Тест: удаление задачи другим пользователем."""
    task = Task(title="Task to delete", user_id="another_user_id")
    test_db.add(task)
    test_db.commit()

    success = delete_task_by_id(test_db, task.id, test_user["id"])
    assert success is False

    db_task = test_db.query(Task).filter(Task.id == task.id).first()
    assert db_task is not None

import pytest
from unittest.mock import patch, AsyncMock
from app.models.task import Task
from app.models.user import User
from app.tasks.notifications import send_task_reminder
from app.utils.email import send_task_email_notification
from app.utils.telegram import send_task_telegram_notification


@pytest.fixture
def mock_user():
    """Создаёт тестового пользователя с email и Telegram chat ID."""
    return User(
        id=1,
        email="test@example.com",
        telegram_chat_id="123456789",
    )


@pytest.fixture
def mock_task_email(mock_user):
    """Создаёт тестовую задачу с email уведомлением."""
    return Task(
        id=1,
        title="Test Task Email",
        description="Test Description",
        email_notification=True,
        telegram_notification=False,
        completed=False,
        user=mock_user,
    )


@pytest.fixture
def mock_task_telegram(mock_user):
    """Создаёт тестовую задачу с Telegram уведомлением."""
    return Task(
        id=2,
        title="Test Task Telegram",
        description="Test Description",
        email_notification=False,
        telegram_notification=True,
        completed=False,
        user=mock_user,
    )


@patch("app.tasks.notifications.SessionLocal")
@patch("app.tasks.notifications.send_task_email_notification")
@patch("app.tasks.notifications.send_task_telegram_notification")
@patch("app.tasks.notifications.get_tasks_with_sms_notifications")
def test_send_task_reminder(
    mock_process_sms,
    mock_process_telegram,
    mock_process_email,
    mock_session,
    mock_task_email,
    mock_task_telegram,
):
    """
    Тестирует отправку напоминаний по email и Telegram.
    """
    # Настройка mock базы данных
    mock_session.return_value.query.return_value.filter.return_value.all.side_effect = [
        [mock_task_email],  # Возвращаем email задачи
        [mock_task_telegram],  # Возвращаем Telegram задачи
    ]

    # Запускаем функцию
    result = send_task_reminder()

    # Проверяем вызовы функций
    mock_process_email.assert_called_once_with(mock_task_email)
    mock_process_telegram.assert_called_once_with(mock_task_telegram)

    # Проверяем результат выполнения
    assert result["status"] == "success"
    assert result["task_count"] == 2


@patch("app.utils.email.send_email")
def test_process_email_notification(mock_send_email, mock_task_email):
    """
    Тестирует обработку уведомлений по email.
    """
    send_task_email_notification(mock_task_email)

    # Проверяем вызов функции send_email с правильными аргументами
    mock_send_email.assert_called_once_with(
        "test@example.com",
        "Напоминание о задаче: Test Task Email",
        "Здравствуйте! Напоминаем вам о задаче:\n\n"
        "Название: Test Task Email\n"
        "Описание: Test Description\n\n"
        "Задача ещё не выполнена. Пожалуйста, завершите её!\n",
    )


@patch("app.core.config.Bot.send_message", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_process_telegram_notification(mock_send_message):
    """
    Тестирует обработку уведомлений через Telegram.
    """
    user = User(id=1, telegram_chat_id="1234567890")
    task = Task(
        id=1,
        title="Test Task Telegram",
        description="Test Description",
        user=user,
    )

    await send_task_telegram_notification(task)

    # Проверяем, что Telegram уведомление отправлено
    mock_send_message.assert_called_once_with(
        chat_id="1234567890",
        text=(
            "Здравствуйте! Напоминаем вам о задаче:\n\n"
            "Название: Test Task Telegram\n"
            "Описание: Test Description\n\n"
            "Задача ещё не выполнена. Пожалуйста, завершите её!\n"
        ),
    )


@patch("app.core.config.Bot.send_message", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_process_telegram_notification_missing_chat_id(mock_send_message):
    """
    Тестирует обработку Telegram уведомлений без chat_id.
    """
    user = User(id=1)  # Пользователь без chat_id
    task = Task(
        id=1,
        title="Test Task Telegram",
        description="Test Description",
        user=user,
    )

    await send_task_telegram_notification(task)

    # Проверяем, что Telegram сообщение НЕ отправлено
    mock_send_message.assert_not_called()


@patch("app.tasks.notifications.send_task_email_notification")
def test_process_email_notification_missing_email(mock_send_email, mock_task_email):
    """
    Тестирует обработку email уведомлений без email у пользователя.
    """
    mock_task_email.user.email = None  # Удаляем email пользователя
    send_task_email_notification(mock_task_email)

    # Проверяем, что email уведомление НЕ отправлено
    mock_send_email.assert_not_called()

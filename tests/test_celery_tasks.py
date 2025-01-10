import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.models.task import Task
from app.models.user import User
from app.tasks import (
    send_task_reminder,
    _process_email_notification,
    _process_telegram_notification,
)


@pytest.fixture
def mock_user():
    """Создаёт тестового пользователя."""
    return User(
        id=1,
        email="test@example.com",
        telegram_chat_id="123456789",
    )


@pytest.fixture
def mock_task_email(mock_user):
    """Создаёт тестовую задачу с уведомлением по email."""
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
    """Создаёт тестовую задачу с уведомлением через Telegram."""
    return Task(
        id=2,
        title="Test Task Telegram",
        description="Test Description",
        email_notification=False,
        telegram_notification=True,
        completed=False,
        user=mock_user,
    )


@patch("app.tasks.SessionLocal")
@patch("app.tasks._process_email_notification")
@patch("app.tasks._process_telegram_notification")
def test_send_task_reminder(
        mock_process_telegram, mock_process_email, mock_session, mock_task_email, mock_task_telegram
):
    """
    Тестирует функцию отправки напоминаний.
    """
    # Мок базы данных
    mock_session.return_value.query.return_value.filter.return_value.all.side_effect = [
        [mock_task_email],  # Email задачи
        [mock_task_telegram],  # Telegram задачи
    ]

    # Запускаем задачу
    result = send_task_reminder()

    # Проверяем вызовы обработчиков
    mock_process_email.assert_called_once_with(mock_task_email)
    mock_process_telegram.assert_called_once_with(mock_task_telegram)

    # Проверяем результат
    assert result["status"] == "success"
    assert result["task_count"] == 2


@patch("app.tasks.send_email")
def test_process_email_notification(mock_send_email, mock_task_email):
    """
    Тестирует обработку уведомлений по email.
    """
    _process_email_notification(mock_task_email)

    # Проверяем, что send_email был вызван с нужными параметрами
    mock_send_email.assert_called_once_with(
        "test@example.com",
        "Напоминание о задаче: Test Task Email",
        "Здравствуйте! Напоминаем вам о задаче:\n\n"
        "Название: Test Task Email\n"
        "Описание: Test Description\n\n"
        "Задача ещё не выполнена. Пожалуйста, завершите её!\n",
    )


@patch("app.tasks.Bot.send_message", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_process_telegram_notification(mock_send_message):
    """
    Тестирует обработку уведомлений через Telegram.
    """
    user = User(id=1, telegram_chat_id="1234567890")
    task = Task(id=1, title="Test Task Telegram", description="Test Description", user=user)

    await _process_telegram_notification(task)

    mock_send_message.assert_called_once_with(
        chat_id="1234567890",
        text=(
            "Здравствуйте! Напоминаем вам о задаче:\n\n"
            "Название: Test Task Telegram\n"
            "Описание: Test Description\n\n"
            "Задача ещё не выполнена. Пожалуйста, завершите её!\n"
        ),
    )


@patch("app.tasks.Bot.send_message", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_process_telegram_notification_missing_chat_id(mock_send_message):
    """
    Тестирует обработку уведомлений через Telegram с отсутствующим chat_id.
    """
    user = User(id=1)
    task = Task(id=1, title="Test Task Telegram", description="Test Description", user=user)

    await _process_telegram_notification(task)

    # Проверяем, что bot.send_message НЕ был вызван
    mock_send_message.assert_not_called()


@patch("app.tasks.send_email")
def test_process_email_notification_missing_email(mock_send_email, mock_task_email):
    """
    Тестирует обработку уведомлений по email с отсутствующим email.
    """
    mock_task_email.user.email = None  # Убираем email
    _process_email_notification(mock_task_email)

    # Проверяем, что send_email НЕ был вызван
    mock_send_email.assert_not_called()

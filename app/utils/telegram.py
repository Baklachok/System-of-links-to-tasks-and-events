from app.core.logger import logger
from app.core.config import bot
from app.models.task import Task
from app.models.user import User
from telegram.error import TelegramError

async def send_task_telegram_notification(task: Task):
    user = task.user
    if not user or not user.telegram_chat_id:
        logger.warning(f"Telegram Chat ID отсутствует для задачи ID {task.id}")
        return

    message = (
        f"Здравствуйте! Напоминаем вам о задаче:\n\n"
        f"Название: {task.title}\n"
        f"Описание: {task.description or 'Без описания'}\n\n"
        f"Задача ещё не выполнена. Пожалуйста, завершите её!\n"
    )

    try:
        logger.info(f"Отправка сообщения в Telegram для задачи ID {task.id}")
        await bot.send_message(chat_id=user.telegram_chat_id, text=message)
    except TelegramError as e:
        logger.error(f"Ошибка отправки сообщения в Telegram для задачи ID {task.id}: {e}")

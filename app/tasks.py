import asyncio
import os
from app.core.celery_app import celery
from app.utils.email import send_email
from app.models.task import Task
from app.models.user import User
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.core.db import SessionLocal
from telegram import Bot
from telegram.error import TelegramError

# Telegram Bot токен из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)


@celery.task
def send_task_reminder():
    """
    Периодическая задача для отправки напоминаний обо всех нерешённых задачах.
    """
    logger.info("Запуск задачи для отправки напоминаний обо всех нерешённых задачах.")
    db: Session = SessionLocal()

    try:
        # Получаем задачи с активными уведомлениями по email
        tasks_email = db.query(Task).filter(
            Task.email_notification == True,
            Task.completed == False,
        ).all()

        # Получаем задачи с активными уведомлениями через Telegram
        tasks_telegram = db.query(Task).filter(
            Task.telegram_notification == True,
            Task.completed == False,
        ).all()

        if not tasks_email and not tasks_telegram:
            logger.info("Нет задач для отправки напоминаний.")
            return {"status": "success", "message": "No tasks to send reminders for."}

        # Отправка напоминаний по email
        for task in tasks_email:
            _process_email_notification(task)

        # Отправка напоминаний через Telegram
        for task in tasks_telegram:
            asyncio.run(_process_telegram_notification(task))

        logger.info("Напоминания обо всех задачах успешно отправлены.")
        return {
            "status": "success",
            "task_count": len(tasks_email) + len(tasks_telegram),
        }

    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()


def _process_email_notification(task: Task):
    """
    Обрабатывает отправку email-уведомления.

    :param task: Объект задачи.
    """
    user = task.user
    if not user or not user.email:
        logger.warning(f"Email пользователя отсутствует для задачи ID {task.id}")
        return

    subject = f"Напоминание о задаче: {task.title}"
    body = (
        f"Здравствуйте! Напоминаем вам о задаче:\n\n"
        f"Название: {task.title}\n"
        f"Описание: {task.description or 'Без описания'}\n\n"
        f"Задача ещё не выполнена. Пожалуйста, завершите её!\n"
    )

    try:
        logger.info(f"Отправка email на {user.email} для задачи ID {task.id}")
        send_email(user.email, subject, body)
    except Exception as e:
        logger.error(f"Ошибка отправки email для задачи ID {task.id}: {e}")


async def _process_telegram_notification(task: Task):
    """
    Обрабатывает отправку уведомления через Telegram.

    :param task: Объект задачи.
    """
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


async def _send_task_reminder(telegram_chat_id: str, body: str):
    """
    Отправляет напоминание в Telegram.

    :param telegram_chat_id: Telegram Chat ID.
    :param body: Сообщение для отправки.
    """
    try:
        await bot.send_message(chat_id=telegram_chat_id, text=body)
    except TelegramError as e:
        logger.error(f"Ошибка отправки Telegram-сообщения: {e}")

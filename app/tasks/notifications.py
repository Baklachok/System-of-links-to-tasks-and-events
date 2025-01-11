import asyncio

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.services.tasks import get_tasks_with_email_notifications, get_tasks_with_telegram_notifications
from app.utils.email import send_task_email_notification
from app.utils.telegram import send_task_telegram_notification
from app.core.logger import logger
from app.core.celery_app import celery


@celery.task
def send_task_reminder():
    """
    Периодическая задача для отправки напоминаний обо всех нерешённых задачах.
    """
    logger.info("Запуск задачи для отправки напоминаний обо всех нерешённых задачах.")
    db: Session = SessionLocal()

    try:
        tasks_email = get_tasks_with_email_notifications(db)
        tasks_telegram = get_tasks_with_telegram_notifications(db)

        if not tasks_email and not tasks_telegram:
            logger.info("Нет задач для отправки напоминаний.")
            return {"status": "success", "message": "No tasks to send reminders for."}

        for task in tasks_email:
            send_task_email_notification(task)

        for task in tasks_telegram:
            asyncio.run(send_task_telegram_notification(task))

        logger.info("Напоминания обо всех задачах успешно отправлены.")
        return {"status": "success", "task_count": len(tasks_email) + len(tasks_telegram)}

    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")
        return {"status": "error", "error": str(e)}

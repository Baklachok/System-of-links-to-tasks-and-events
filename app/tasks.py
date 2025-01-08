from datetime import datetime, timedelta

from app.core.celery_app import celery
from app.utils.email import send_email
from app.models.task import Task
from app.models.user import User
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.core.db import SessionLocal


@celery.task
def send_task_reminder():
    """
    Периодическая задача для отправки напоминаний для всех активных задач.
    """
    logger.info("Запуск задачи для отправки напоминаний обо всех нерешённых задачах.")
    db: Session = SessionLocal()

    try:
        # Получаем задачи, которые не выполнены и подходят под критерии
        tasks = db.query(Task).filter(
            Task.email_notification == True, # Уведомления включены
            Task.completed == False,  # Задача не завершена
        ).all()

        if not tasks:
            logger.info("Нет задач, подходящих для отправки напоминаний.")
            return {"status": "success", "message": "No tasks to send reminders for."}

        # Обрабатываем каждую задачу
        for task in tasks:
            user_email = task.user.email if task.user else None

            if not user_email:
                logger.warning(f"У задачи ID {task.id} отсутствует email пользователя.")
                continue

            # Формируем и отправляем напоминание
            subject = f"Напоминание о задаче: {task.title}"
            body = f"""Здравствуйте! Напоминаем вам о задаче:

            Название: {task.title}
            Описание: {task.description}
            
            Задача ещё не выполнена. Пожалуйста, завершите её!
            """

            try:
                logger.info(f"Отправка напоминания на {user_email} для задачи ID {task.id}")
                send_email(user_email, subject, body)
            except Exception as e:
                logger.error(f"Ошибка отправки email для задачи ID {task.id}: {e}")

        logger.info("Напоминания обо всех задачах успешно отправлены.")
        return {"status": "success", "task_count": len(tasks)}

    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

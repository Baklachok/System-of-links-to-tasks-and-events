from app.core.celery_app import celery
from app.utils.email import send_email
from app.core.logger import logger  # Импортируем логгер


@celery.task
def send_email_notification(task_id: int):
    """
    Асинхронная задача для отправки email.
    """
    logger.info(f"Начало выполнения задачи отправки email для задачи ID {task_id}")

    # Имитация получения email пользователя
    try:
        user_email = "korobko_01@inbox.ru"
        subject = "Уведомление о задаче"
        body = f"Ваша задача с ID {task_id} выполнена!"

        logger.info(f"Отправка email на адрес {user_email} с темой '{subject}'")

        # Отправляем письмо
        send_email(user_email, subject, body)

        logger.info(f"Email успешно отправлен на адрес {user_email} для задачи ID {task_id}")
        return {"status": "success", "task_id": task_id}
    except Exception as e:
        logger.error(f"Ошибка при отправке email для задачи ID {task_id}: {e}")
        return {"status": "error", "task_id": task_id, "error": str(e)}

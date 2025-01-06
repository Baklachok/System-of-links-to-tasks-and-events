from fastapi import APIRouter
from app.tasks import send_email_notification
from app.core.logger import logger  # Импортируем логгер

router = APIRouter()


@router.post("/notify/")
async def notify_user(task_id: int):
    """
    Создаёт задачу для отправки email-уведомления.
    """
    logger.info(f"Получен запрос на отправку уведомления для задачи ID {task_id}")

    try:
        # Запускаем задачу через Celery
        result = send_email_notification.delay(task_id)
        logger.info(f"Создана задача Celery с ID {result.id} для отправки уведомления")

        return {"task_id": result.id, "status": "Notification task created"}
    except Exception as e:
        logger.error(f"Ошибка при создании задачи для уведомления: {e}")
        return {"error": "Failed to create notification task"}

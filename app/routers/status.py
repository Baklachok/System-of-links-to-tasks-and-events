from fastapi import APIRouter
from app.core.celery_app import celery

router = APIRouter()

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    Проверяет статус задачи отправки уведомления.
    """
    result = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
    }

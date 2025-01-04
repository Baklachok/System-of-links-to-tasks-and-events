from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.logger import logger
from app.schemas.tasks import Task, TaskCreate, TaskUpdate
from app.services.tasks import (
    get_all_tasks_for_user,
    create_task,
    get_task_by_id,
    update_task,
    delete_task,
)
from app.schemas.auth import UserResponse
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/tasks", response_model=List[Task])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Получить все задачи для текущего пользователя.
    """
    logger.info(f"Получение всех задач для пользователя ID {current_user.id}")
    tasks = get_all_tasks_for_user(db, current_user.id)
    logger.info(f"Найдено задач: {len(tasks)}")
    return tasks


@router.post("/tasks", response_model=Task)
def create_new_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Создать новую задачу для текущего пользователя.
    """
    logger.info(f"Создание новой задачи для пользователя ID {current_user.id}")
    new_task = create_task(db, task, current_user.id)
    logger.info(f"Задача создана с ID {new_task.id}")
    return new_task


@router.get("/tasks/{task_id}", response_model=Task)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Получить задачу по ID, принадлежащую текущему пользователю.
    """
    logger.info(f"Получение задачи ID {task_id} для пользователя ID {current_user.id}")
    task = get_task_by_id(db, task_id, current_user.id)
    if not task:
        logger.warning(f"Задача ID {task_id} не найдена для пользователя ID {current_user.id}")
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info(f"Задача ID {task.id} успешно получена")
    return task


@router.put("/tasks/{task_id}", response_model=Task)
def update_existing_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Обновить задачу, принадлежащую текущему пользователю.
    """
    logger.info(f"Обновление задачи ID {task_id} для пользователя ID {current_user.id}")
    updated_task = update_task(db, task_id, task, current_user.id)
    if not updated_task:
        logger.warning(f"Задача ID {task_id} не найдена для обновления")
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info(f"Задача ID {updated_task.id} успешно обновлена")
    return updated_task


@router.delete("/tasks/{task_id}")
def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Удалить задачу, принадлежащую текущему пользователю.
    """
    logger.info(f"Удаление задачи ID {task_id} для пользователя ID {current_user.id}")
    if not delete_task(db, task_id, current_user.id):
        logger.warning(f"Задача ID {task_id} не найдена для удаления")
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info(f"Задача ID {task_id} успешно удалена")
    return {"message": "Task deleted successfully"}

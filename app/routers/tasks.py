from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.logger import logger
from app.schemas.tasks import Task, TaskCreate, TaskUpdate
from app.services.tasks import (
    get_tasks_by_user_id,
    create_task_for_user,
    get_task_by_id_and_user,
    update_task_by_id,
    delete_task_by_id,
)
from app.schemas.auth import UserResponse
from app.services.auth import get_current_user

router = APIRouter()


def validate_task_existence(task, task_id, user_id):
    """
    Проверить существование задачи и выбросить исключение, если задача не найдена.
    """
    if not task:
        logger.warning(f"Задача ID {task_id} не найдена для пользователя ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )


@router.get("/tasks", response_model=List[Task])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Получить все задачи текущего пользователя.
    """
    logger.info(f"Получение задач для пользователя ID {current_user.id}")
    tasks = get_tasks_by_user_id(db, current_user.id)
    logger.info(f"Найдено {len(tasks)} задач для пользователя ID {current_user.id}")
    return tasks


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Создать новую задачу для текущего пользователя.
    """
    logger.info(f"Создание новой задачи для пользователя ID {current_user.id}")
    new_task = create_task_for_user(db, task_data, current_user.id)
    logger.info(f"Задача создана с ID {new_task.id} для пользователя ID {current_user.id}")
    return new_task


@router.get("/tasks/{task_id}", response_model=Task)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Получить задачу по ID текущего пользователя.
    """
    logger.info(f"Получение задачи ID {task_id} для пользователя ID {current_user.id}")
    task = get_task_by_id_and_user(db, task_id, current_user.id)
    validate_task_existence(task, task_id, current_user.id)
    logger.info(f"Задача ID {task.id} успешно получена для пользователя ID {current_user.id}")
    return task


@router.put("/tasks/{task_id}", response_model=Task)
def update_existing_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Обновить задачу текущего пользователя по ID.
    """
    logger.info(f"Обновление задачи ID {task_id} для пользователя ID {current_user.id}")
    task = update_task_by_id(db, task_id, task_data, current_user.id)
    validate_task_existence(task, task_id, current_user.id)
    logger.info(f"Задача ID {task.id} успешно обновлена для пользователя ID {current_user.id}")
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Удалить задачу текущего пользователя по ID.
    """
    logger.info(f"Удаление задачи ID {task_id} для пользователя ID {current_user.id}")
    success = delete_task_by_id(db, task_id, current_user.id)
    if not success:
        validate_task_existence(None, task_id, current_user.id)
    logger.info(f"Задача ID {task_id} успешно удалена для пользователя ID {current_user.id}")

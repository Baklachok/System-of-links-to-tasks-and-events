from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional

from app.core.logger import logger
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate


def get_tasks_by_user_id(db: Session, user_id: str) -> List[Task]:
    """
    Получить все задачи для определённого пользователя.
    """
    logger.info(f"Получение всех задач для пользователя: {user_id}")
    try:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        logger.info(f"Найдено задач: {len(tasks)}")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении задач для пользователя {user_id}: {e}")
        raise


def create_task_for_user(db: Session, task: TaskCreate, user_id: str) -> Task:
    """
    Создать новую задачу для пользователя.
    """
    logger.info(f"Создание задачи для пользователя: {user_id}, данные: {task.dict()}")
    try:
        db_task = Task(**task.dict(exclude={"user_id"}), user_id=user_id)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        logger.info(f"Задача создана: {db_task.id}")
        return db_task
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Ошибка при создании задачи для пользователя {user_id}: {e}")
        raise


def get_task_by_id_and_user(db: Session, task_id: int, user_id: str) -> Optional[Task]:
    """
    Получить задачу по ID, принадлежащую пользователю.
    """
    logger.info(f"Получение задачи по ID: {task_id} для пользователя: {user_id}")
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if task:
            logger.info(f"Задача найдена: {task.id}")
        else:
            logger.warning(f"Задача с ID {task_id} не найдена для пользователя {user_id}")
        return task
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении задачи ID {task_id} для пользователя {user_id}: {e}")
        raise


def update_task_by_id(db: Session, task_id: int, task_data: TaskUpdate, user_id: str) -> Optional[Task]:
    """
    Обновить задачу по ID, если она принадлежит пользователю.
    """
    logger.info(
        f"Обновление задачи ID: {task_id} для пользователя: {user_id}, данные: {task_data.dict(exclude_unset=True)}"
    )
    db_task = get_task_by_id_and_user(db, task_id, user_id)
    if not db_task:
        logger.warning(f"Задача с ID {task_id} не найдена для обновления")
        return None

    try:
        for key, value in task_data.dict(exclude_unset=True).items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
        logger.info(f"Задача обновлена: {db_task.id}")
        return db_task
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении задачи ID {task_id}: {e}")
        raise


def delete_task_by_id(db: Session, task_id: int, user_id: str) -> bool:
    """
    Удалить задачу по ID, если она принадлежит пользователю.
    """
    logger.info(f"Удаление задачи ID: {task_id} для пользователя: {user_id}")
    db_task = get_task_by_id_and_user(db, task_id, user_id)
    if not db_task:
        logger.warning(f"Задача с ID {task_id} не найдена для удаления")
        return False

    try:
        db.delete(db_task)
        db.commit()
        logger.info(f"Задача удалена: {task_id}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Ошибка при удалении задачи ID {task_id}: {e}")
        raise

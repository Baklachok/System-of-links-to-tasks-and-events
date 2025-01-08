from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.logger import logger
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate


def get_tasks_by_user_id(db: Session, user_id: str) -> List[Task]:
    """
    Получить все задачи пользователя.
    """
    logger.info(f"Получение всех задач для пользователя: {user_id}")
    try:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        logger.info(f"Найдено задач: {len(tasks)} для пользователя {user_id}")
        return tasks
    except SQLAlchemyError as e:
        logger.exception(f"Ошибка при получении задач для пользователя {user_id}: {e}")
        raise


def create_task_for_user(db: Session, task: TaskCreate, user_id: str) -> Task:
    """
    Создать задачу для пользователя.
    """
    logger.info(f"Создание задачи для пользователя {user_id}: {task.dict()}")
    try:
        db_task = Task(**task.dict(), user_id=user_id)
        db.add(db_task)
        db.flush()  # Генерация ID
        logger.info(f"Задача успешно создана с ID {db_task.id} для пользователя {user_id}")
        return db_task
    except SQLAlchemyError as e:
        logger.exception(f"Ошибка при создании задачи для пользователя {user_id}: {e}")
        raise


def get_task_by_id_and_user(db: Session, task_id: int, user_id: str) -> Optional[Task]:
    """
    Получить задачу по ID и пользователю.
    """
    logger.info(f"Получение задачи ID {task_id} для пользователя {user_id}")
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if task:
            logger.info(f"Задача найдена: {task.id} для пользователя {user_id}")
        else:
            logger.warning(f"Задача ID {task_id} не найдена для пользователя {user_id}")
        return task
    except SQLAlchemyError as e:
        logger.exception(f"Ошибка при получении задачи ID {task_id} для пользователя {user_id}: {e}")
        raise


def update_task_by_id(db: Session, task_id: int, task_data: TaskUpdate, user_id: str) -> Optional[Task]:
    """
    Обновить задачу по ID и пользователю.
    """
    logger.info(f"Обновление задачи ID {task_id} для пользователя {user_id}")
    task = get_task_by_id_and_user(db, task_id, user_id)
    if not task:
        logger.warning(f"Задача ID {task_id} не найдена для обновления пользователем {user_id}")
        return None

    try:
        for key, value in task_data.dict(exclude_unset=True).items():
            setattr(task, key, value)
        db.flush()  # Применение изменений
        logger.info(f"Задача ID {task.id} успешно обновлена для пользователя {user_id}")
        return task
    except SQLAlchemyError as e:
        logger.exception(f"Ошибка при обновлении задачи ID {task_id}: {e}")
        raise


def delete_task_by_id(db: Session, task_id: int, user_id: str) -> bool:
    """
    Удалить задачу по ID и пользователю.
    """
    logger.info(f"Удаление задачи ID {task_id} для пользователя {user_id}")
    task = get_task_by_id_and_user(db, task_id, user_id)
    if not task:
        logger.warning(f"Задача ID {task_id} не найдена для удаления пользователем {user_id}")
        return False

    try:
        db.delete(task)
        db.commit()
        logger.info(f"Задача ID {task_id} успешно удалена для пользователя {user_id}")
        return True
    except SQLAlchemyError as e:
        logger.exception(f"Ошибка при удалении задачи ID {task_id}: {e}")
        raise

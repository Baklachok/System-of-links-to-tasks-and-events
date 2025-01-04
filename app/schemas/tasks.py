from pydantic import BaseModel
from typing import Optional


class TaskBase(BaseModel):
    """
    Базовая схема задачи.
    """
    title: str
    description: Optional[str] = None
    completed: bool = False


class TaskCreate(TaskBase):
    """
    Схема для создания задачи.
    """
    user_id: str  # Указываем ID пользователя, создающего задачу.


class TaskUpdate(BaseModel):
    """
    Схема для обновления задачи.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class Task(TaskBase):
    """
    Схема задачи для ответа.
    """
    id: int
    user_id: str  # ID пользователя, к которому привязана задача.

    class Config:
        orm_mode = True

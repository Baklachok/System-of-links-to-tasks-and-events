from pydantic import BaseModel
from typing import Optional


class TaskBase(BaseModel):
    """
    Базовая схема задачи.
    """
    title: str
    description: Optional[str] = None
    completed: bool = False
    email_notification: bool = False
    telegram_notification: bool = False
    sms_notification: bool = False


class TaskCreate(TaskBase):
    """
    Схема для создания задачи.
    """
    pass


class TaskUpdate(BaseModel):
    """
    Схема для обновления задачи.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    email_notification: Optional[bool] = None
    telegram_notification: Optional[bool] = None
    sms_notification: Optional[bool] = None


class Task(TaskBase):
    """
    Схема задачи для ответа.
    """
    id: int
    user_id: str  # ID пользователя, к которому привязана задача.

    class Config:
        orm_mode = True

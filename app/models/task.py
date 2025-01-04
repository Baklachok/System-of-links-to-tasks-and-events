from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class Task(Base):
    """
    Модель задачи в базе данных.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)

    # Связь с пользователем через user_id
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Реляция для доступа к данным пользователя
    user = relationship("User", back_populates="tasks")

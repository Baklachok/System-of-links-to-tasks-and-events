from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.core.db import Base


class User(Base):
    """
    Модель пользователя в базе данных.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Реляция для связи с задачами
    tasks = relationship("Task", back_populates="user")

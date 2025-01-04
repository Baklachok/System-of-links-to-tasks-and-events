from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.logger import logger

# Подключение к базе данных
DATABASE_URL = "postgresql+psycopg://user:password@postgres:5432/mydatabase"

logger.info(f"Подключение к базе данных: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


# Функция для получения сессии базы данных
def get_db():
    logger.info("Создание новой сессии базы данных")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        raise
    finally:
        logger.info("Закрытие сессии базы данных")
        db.close()

from app.db import Base, engine
from app.models.user import User  # Импортируйте все модели, которые вы хотите создать

# Создание всех таблиц в базе данных
def init_db():
    print("Создаем таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы.")
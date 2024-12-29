from app.core.db import Base, engine


# Создание всех таблиц в базе данных
def init_db():
    print("Создаем таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы.")
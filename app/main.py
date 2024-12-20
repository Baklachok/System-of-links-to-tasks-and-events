from fastapi import FastAPI

# Создаем экземпляр FastAPI
app = FastAPI()

# Определяем корневой роут
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI!"}

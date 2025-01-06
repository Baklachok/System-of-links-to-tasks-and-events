from fastapi import FastAPI

from app.core.init_db import init_db
from app.routers import auth, tasks, notifications, status

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(notifications.router)
app.include_router(status.router)

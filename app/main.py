from fastapi import FastAPI

from app.init_db import init_db
from app.routers import auth

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(auth.router)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.schemas.tasks import Task, TaskCreate, TaskUpdate
from app.services.tasks import get_all_tasks, create_task, get_task_by_id, update_task, delete_task

router = APIRouter()

@router.get("/tasks", response_model=List[Task])
def list_tasks(db: Session = Depends(get_db)):
    return get_all_tasks(db)

@router.post("/tasks", response_model=Task)
def create_new_task(task: TaskCreate, db: Session = Depends(get_db)):
    return create_task(db, task)

@router.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=Task)
def update_existing_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    updated_task = update_task(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@router.delete("/tasks/{task_id}")
def delete_existing_task(task_id: int, db: Session = Depends(get_db)):
    if not delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

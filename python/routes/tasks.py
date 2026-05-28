# routes/tasks.py — Task CRUD endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.task_manager import (
    create_task, get_all_tasks, get_task,
    complete_task, delete_task, update_task, search_tasks
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ── Models ─────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title:       str
    description: Optional[str] = ""
    priority:    Optional[str] = "normal"   # low | normal | high
    due_date:    Optional[str] = None       # ISO 8601 string

class TaskUpdate(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None
    priority:    Optional[str] = None
    due_date:    Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/")
async def create(task: TaskCreate):
    """Create a new task."""
    return create_task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date
    )

@router.get("/")
async def get_all(status: Optional[str] = None):
    """Get all tasks. Filter by ?status=pending or ?status=done"""
    return get_all_tasks(status=status)

@router.get("/search")
async def search(q: str):
    """Search tasks by title or description."""
    return search_tasks(q)

@router.get("/{task_id}")
async def get_one(task_id: int):
    """Get a single task by ID."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}/complete")
async def complete(task_id: int):
    """Mark a task as done."""
    task = complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}")
async def update(task_id: int, data: TaskUpdate):
    """Update task fields."""
    task = update_task(task_id, **data.model_dump(exclude_none=True))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}")
async def delete(task_id: int):
    """Delete a task."""
    success = delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True, "id": task_id}
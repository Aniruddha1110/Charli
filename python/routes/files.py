# routes/files.py — File Manager endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.file_manager import (
    search_files, list_directory, open_file,
    rename_file, move_file, delete_file,
    create_folder, get_file_info
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/files", tags=["Files"])


# ── Models ─────────────────────────────────────────────────────────────────

class RenameRequest(BaseModel):
    path:     str
    new_name: str

class MoveRequest(BaseModel):
    path:        str
    destination: str

class DeleteRequest(BaseModel):
    path:  str
    trash: Optional[bool] = True

class OpenRequest(BaseModel):
    path: str

class CreateFolderRequest(BaseModel):
    path: str


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/search")
async def search(q: str, max_results: int = 20):
    """
    Search for files by name across Desktop, Documents, Downloads etc.
    GET /files/search?q=resume
    """
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = search_files(q.strip(), max_results=max_results)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/list")
async def list_dir(path: str):
    """
    List contents of a directory.
    GET /files/list?path=C:/Users/KIIT/Desktop
    """
    result = list_directory(path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/open")
async def open_item(request: OpenRequest):
    """Open a file or folder with its default application."""
    result = open_file(request.path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/rename")
async def rename(request: RenameRequest):
    """Rename a file or folder."""
    result = rename_file(request.path, request.new_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/move")
async def move(request: MoveRequest):
    """Move a file or folder to a new location."""
    result = move_file(request.path, request.destination)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/delete")
async def delete(request: DeleteRequest):
    """Delete a file. Sends to recycle bin by default."""
    result = delete_file(request.path, request.trash)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/create-folder")
async def create(request: CreateFolderRequest):
    """Create a new folder."""
    result = create_folder(request.path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/info")
async def info(path: str):
    """Get detailed info about a file or folder."""
    result = get_file_info(path)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/quick")
async def quick_folders():
    """Return quick access folders — Desktop, Documents, Downloads etc."""
    import os
    folders = [
        {"name": "Desktop",   "path": os.path.expanduser("~\\Desktop")},
        {"name": "Documents", "path": os.path.expanduser("~\\Documents")},
        {"name": "Downloads", "path": os.path.expanduser("~\\Downloads")},
        {"name": "Pictures",  "path": os.path.expanduser("~\\Pictures")},
        {"name": "Music",     "path": os.path.expanduser("~\\Music")},
        {"name": "Videos",    "path": os.path.expanduser("~\\Videos")},
    ]
    return {"folders": [f for f in folders if os.path.exists(f["path"])]}
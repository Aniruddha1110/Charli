# routes/automation.py — Automation endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.automation import (
    open_app, type_text, press_key,
    take_screenshot, save_screenshot,
    get_volume, set_volume, mute_volume,
    get_clipboard, set_clipboard,
    run_command, list_processes,
    APP_REGISTRY
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/automation", tags=["Automation"])


# ── Models ─────────────────────────────────────────────────────────────────

class OpenAppRequest(BaseModel):
    app_name: str

class TypeTextRequest(BaseModel):
    text:  str
    delay: Optional[float] = 0.05

class PressKeyRequest(BaseModel):
    key: str

class ScreenshotRequest(BaseModel):
    region: Optional[dict] = None
    save:   Optional[bool] = False
    path:   Optional[str]  = None

class VolumeRequest(BaseModel):
    level: int

class MuteRequest(BaseModel):
    mute: bool

class ClipboardWriteRequest(BaseModel):
    text: str

class CommandRequest(BaseModel):
    command: str
    timeout: Optional[int] = 30


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/apps")
async def get_apps():
    """Get list of known apps Charli can open."""
    apps = sorted(set(APP_REGISTRY.keys()))
    return {"apps": apps, "count": len(apps)}

@router.post("/open")
async def open_application(request: OpenAppRequest):
    """Open an application by name."""
    result = open_app(request.app_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/type")
async def type_text_endpoint(request: TypeTextRequest):
    """Type text into the active window."""
    result = type_text(request.text, request.delay)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/key")
async def press_key_endpoint(request: PressKeyRequest):
    """Press a key or hotkey combination."""
    result = press_key(request.key)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/screenshot")
async def screenshot(request: ScreenshotRequest):
    """Take a screenshot."""
    if request.save:
        result = save_screenshot(request.path)
    else:
        result = take_screenshot(request.region)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/volume")
async def volume_get():
    """Get current volume level."""
    return get_volume()

@router.post("/volume")
async def volume_set(request: VolumeRequest):
    """Set volume level (0-100)."""
    result = set_volume(request.level)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/volume/mute")
async def volume_mute(request: MuteRequest):
    """Mute or unmute volume."""
    result = mute_volume(request.mute)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/clipboard")
async def clipboard_read():
    """Read clipboard content."""
    return get_clipboard()

@router.post("/clipboard")
async def clipboard_write(request: ClipboardWriteRequest):
    """Write text to clipboard."""
    result = set_clipboard(request.text)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/command")
async def run_cmd(request: CommandRequest):
    """Run a terminal command."""
    result = run_command(request.command, request.timeout)
    return result

@router.get("/processes")
async def processes(filter: str = ""):
    """List running processes."""
    return list_processes(filter)
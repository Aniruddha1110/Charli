# automation.py — Desktop automation for Charli
# Open apps, type text, screenshot, volume, clipboard, run commands.

import os
import subprocess
import time
import base64
import io
import pyautogui
import pyperclip
from PIL import ImageGrab
from utils.logger import get_logger

logger = get_logger(__name__)

# Disable pyautogui failsafe for smoother automation
pyautogui.FAILSAFE = False
pyautogui.PAUSE    = 0.1


# ── Known apps registry ────────────────────────────────────────────────────
# Maps friendly names to executable paths or commands
APP_REGISTRY = {
    # Browsers
    "chrome":         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome":  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":        r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "brave":          r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",

    # Dev tools
    "vs code":        "code",
    "vscode":         "code",
    "visual studio code": "code",
    "notepad":        "notepad",
    "notepad++":      r"C:\Program Files\Notepad++\notepad++.exe",

    # Terminals — use START so a visible window opens
    "cmd":            "__CMD__",
    "terminal":       "__CMD__",
    "powershell":     "__POWERSHELL__",

    # Media
    "spotify":        "spotify",
    "vlc":            r"C:\Program Files\VideoLAN\VLC\vlc.exe",

    # System
    "file explorer":  "explorer",
    "explorer":       "explorer",
    "task manager":   "taskmgr",
    "control panel":  "control",
    "settings":       "ms-settings:",
    "calculator":     "calc",
    "paint":          "mspaint",
    "snipping tool":  "snippingtool",

    # Office
    "word":       r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":      r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "outlook":    r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",

    # Communication — UWP Store apps
    "whatsapp":   "__UWP__5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "telegram":   "__UWP__TelegramMessengerLLP.TelegramDesktop_t4vj0pshhgkwm!App",

    # Discord — needs Update.exe with flag
    "discord":    r"C:\Users\KIIT\AppData\Local\Discord\Update.exe --processStart Discord.exe",

    "zoom":       r"C:\Users\KIIT\AppData\Roaming\Zoom\bin\Zoom.exe",
    "teams":      r"C:\Users\KIIT\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "slack":      r"C:\Users\KIIT\AppData\Local\slack\slack.exe",
}


# ── Open app ───────────────────────────────────────────────────────────────

def open_app(app_name: str) -> dict:
    app_lower = app_name.lower().strip()
    logger.info(f"Opening app: '{app_name}'")

    cmd = APP_REGISTRY.get(app_lower, app_lower)

    try:
        # ── UWP / Microsoft Store apps ─────────────────────────────────
        if cmd.startswith("__UWP__"):
            family = cmd.replace("__UWP__", "")
            shell_url = f"shell:AppsFolder\\{family}"
            subprocess.Popen(
                ["explorer.exe", shell_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Launched UWP: {shell_url}")
            return {"success": True, "app": app_name, "command": shell_url}

        # ── ms-settings: ───────────────────────────────────────────────
        if cmd.startswith("ms-settings:"):
            os.startfile(cmd)
            return {"success": True, "app": app_name, "command": cmd}

        # ── CMD — needs 'start' to open a visible window ───────────────
        if cmd == "__CMD__":
            subprocess.Popen(
                "start cmd",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Launched CMD")
            return {"success": True, "app": app_name, "command": "start cmd"}

        # ── PowerShell — same issue as CMD ─────────────────────────────
        if cmd == "__POWERSHELL__":
            subprocess.Popen(
                r'start C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Launched PowerShell")
            return {"success": True, "app": app_name, "command": "start powershell"}

        # ── Regular .exe path or short command ─────────────────────────
        subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(f"Launched: {cmd}")
        return {"success": True, "app": app_name, "command": cmd}

    except Exception as e:
        logger.error(f"Failed to open {app_name}: {e}")
        return {"success": False, "app": app_name, "error": str(e)}


# ── Type text ──────────────────────────────────────────────────────────────

def type_text(text: str, delay: float = 0.05) -> dict:
    """
    Type text into the currently active window.
    Waits 1 second before typing to give user time to focus the target.
    """
    logger.info(f"Typing text: '{text[:50]}'")
    try:
        time.sleep(1)   # Give user time to click into target window
        pyautogui.write(text, interval=delay)
        return {"success": True, "text": text}
    except Exception as e:
        logger.error(f"Type text failed: {e}")
        return {"success": False, "error": str(e)}


def press_key(key: str) -> dict:
    """Press a keyboard key or hotkey combination."""
    logger.info(f"Pressing key: '{key}'")
    try:
        keys = [k.strip() for k in key.lower().split("+")]
        if len(keys) > 1:
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(keys[0])
        return {"success": True, "key": key}
    except Exception as e:
        logger.error(f"Key press failed: {e}")
        return {"success": False, "error": str(e)}


# ── Screenshot ─────────────────────────────────────────────────────────────

def take_screenshot(region: dict = None) -> dict:
    """
    Take a screenshot of the full screen or a region.

    Args:
        region: Optional dict with x, y, width, height for region capture

    Returns:
        Dict with base64 encoded PNG image
    """
    logger.info("Taking screenshot")
    try:
        if region:
            bbox = (
                region["x"],
                region["y"],
                region["x"] + region["width"],
                region["y"] + region["height"],
            )
            img = ImageGrab.grab(bbox=bbox)
        else:
            img = ImageGrab.grab()

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        logger.info(f"Screenshot taken: {img.size}")
        return {
            "success": True,
            "image":   b64,
            "width":   img.size[0],
            "height":  img.size[1],
            "format":  "png",
        }
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return {"success": False, "error": str(e)}


def save_screenshot(path: str = None) -> dict:
    """Take and save a screenshot to disk."""
    import os
    from datetime import datetime

    if not path:
        desktop = os.path.expanduser("~\\Desktop")
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        path    = os.path.join(desktop, f"screenshot_{ts}.png")

    try:
        img = ImageGrab.grab()
        img.save(path)
        logger.info(f"Screenshot saved: {path}")
        return {"success": True, "path": path}
    except Exception as e:
        logger.error(f"Save screenshot failed: {e}")
        return {"success": False, "error": str(e)}


# ── Volume control ─────────────────────────────────────────────────────────

def get_volume() -> dict:
    """Get current system volume level (0-100)."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = round(volume.GetMasterVolumeLevelScalar() * 100)
        muted   = bool(volume.GetMute())

        return {"success": True, "volume": current, "muted": muted}
    except Exception as e:
        logger.error(f"Get volume failed: {e}")
        return {"success": False, "error": str(e)}


def set_volume(level: int) -> dict:
    """
    Set system volume to a specific level (0-100).
    """
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        level = max(0, min(100, level))

        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = cast(interface, POINTER(IAudioEndpointVolume))

        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        logger.info(f"Volume set to {level}%")
        return {"success": True, "volume": level}
    except Exception as e:
        logger.error(f"Set volume failed: {e}")
        return {"success": False, "error": str(e)}


def mute_volume(mute: bool = True) -> dict:
    """Mute or unmute system volume."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = cast(interface, POINTER(IAudioEndpointVolume))

        volume.SetMute(1 if mute else 0, None)
        logger.info(f"Volume {'muted' if mute else 'unmuted'}")
        return {"success": True, "muted": mute}
    except Exception as e:
        logger.error(f"Mute failed: {e}")
        return {"success": False, "error": str(e)}


# ── Clipboard ──────────────────────────────────────────────────────────────

def get_clipboard() -> dict:
    """Read current clipboard content."""
    try:
        content = pyperclip.paste()
        logger.info(f"Clipboard read: {len(content)} chars")
        return {"success": True, "content": content, "length": len(content)}
    except Exception as e:
        logger.error(f"Clipboard read failed: {e}")
        return {"success": False, "error": str(e)}


def set_clipboard(text: str) -> dict:
    """Write text to clipboard."""
    try:
        pyperclip.copy(text)
        logger.info(f"Clipboard written: {len(text)} chars")
        return {"success": True, "content": text}
    except Exception as e:
        logger.error(f"Clipboard write failed: {e}")
        return {"success": False, "error": str(e)}


# ── Run command ────────────────────────────────────────────────────────────

def run_command(command: str, timeout: int = 30) -> dict:
    """
    Execute a terminal command and return output.

    Args:
        command: Shell command to run
        timeout: Max seconds to wait

    Returns:
        Dict with stdout, stderr, return code
    """
    logger.info(f"Running command: '{command}'")

    # Safety check — block dangerous commands
    blocked = [
        "format", "del /f /s", "rm -rf", "rmdir /s",
        "shutdown", "reg delete", "rd /s /q c:\\",
    ]
    for b in blocked:
        if b.lower() in command.lower():
            return {
                "success": False,
                "error":   f"Command blocked for safety: contains '{b}'"
            }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success":     result.returncode == 0,
            "stdout":      result.stdout.strip(),
            "stderr":      result.stderr.strip(),
            "return_code": result.returncode,
            "command":     command,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return {"success": False, "error": str(e)}


# ── List running processes ─────────────────────────────────────────────────

def list_processes(filter_name: str = "") -> dict:
    """List running processes, optionally filtered by name."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = p.info
                if filter_name.lower() in info["name"].lower():
                    procs.append({
                        "pid":    info["pid"],
                        "name":   info["name"],
                        "cpu":    info["cpu_percent"],
                        "memory": info["memory_info"].rss // (1024 * 1024),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda x: x["memory"], reverse=True)
        return {"success": True, "processes": procs[:50]}
    except Exception as e:
        return {"success": False, "error": str(e)}
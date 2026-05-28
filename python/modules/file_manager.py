# file_manager.py — File operations for Charli
# Search, open, move, rename, delete, list files and folders.

import os
import shutil
import subprocess
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

# Common search locations — searches these by default
DEFAULT_SEARCH_ROOTS = [
    os.path.expanduser("~\\Desktop"),
    os.path.expanduser("~\\Documents"),
    os.path.expanduser("~\\Downloads"),
    os.path.expanduser("~\\Pictures"),
    os.path.expanduser("~\\Music"),
    os.path.expanduser("~\\Videos"),
]


def search_files(query: str, roots: list[str] = None, max_results: int = 20) -> list[dict]:
    """
    Search for files by name across common user directories.

    Args:
        query:       Filename or partial name to search for
        roots:       List of directories to search (defaults to common folders)
        max_results: Maximum number of results to return

    Returns:
        List of file info dicts
    """
    if not roots:
        roots = [r for r in DEFAULT_SEARCH_ROOTS if os.path.exists(r)]

    results = []
    query_lower = query.lower()

    for root in roots:
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                # Skip hidden folders
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]

                for filename in filenames:
                    if query_lower in filename.lower():
                        full_path = os.path.join(dirpath, filename)
                        try:
                            stat = os.stat(full_path)
                            results.append({
                                "name":     filename,
                                "path":     full_path,
                                "size":     stat.st_size,
                                "size_str": _format_size(stat.st_size),
                                "modified": stat.st_mtime,
                                "type":     _get_file_type(filename),
                                "folder":   dirpath,
                            })
                        except (PermissionError, OSError):
                            continue

                        if len(results) >= max_results:
                            return sorted(results, key=lambda x: x["modified"], reverse=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot access {root}: {e}")

    return sorted(results, key=lambda x: x["modified"], reverse=True)


def list_directory(path: str) -> dict:
    """
    List contents of a directory.

    Args:
        path: Directory path to list

    Returns:
        Dict with folders and files lists
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return {"error": f"Path does not exist: {path}"}

    if not os.path.isdir(path):
        return {"error": f"Not a directory: {path}"}

    folders = []
    files   = []

    try:
        for entry in sorted(os.scandir(path), key=lambda e: e.name.lower()):
            try:
                stat = entry.stat()
                info = {
                    "name":     entry.name,
                    "path":     entry.path,
                    "modified": stat.st_mtime,
                }
                if entry.is_dir():
                    folders.append(info)
                else:
                    info["size"]     = stat.st_size
                    info["size_str"] = _format_size(stat.st_size)
                    info["type"]     = _get_file_type(entry.name)
                    files.append(info)
            except (PermissionError, OSError):
                continue
    except PermissionError:
        return {"error": f"Permission denied: {path}"}

    return {
        "path":    path,
        "folders": folders,
        "files":   files,
        "total":   len(folders) + len(files),
    }


def open_file(path: str) -> dict:
    """
    Open a file or folder with the default Windows application.

    Args:
        path: Full path to file or folder

    Returns:
        Success or error dict
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return {"success": False, "error": f"Path does not exist: {path}"}

    try:
        os.startfile(path)
        logger.info(f"Opened: {path}")
        return {"success": True, "path": path}
    except Exception as e:
        logger.error(f"Failed to open {path}: {e}")
        return {"success": False, "error": str(e)}


def rename_file(path: str, new_name: str) -> dict:
    """
    Rename a file or folder.

    Args:
        path:     Full path to the file
        new_name: New filename (not full path, just the name)

    Returns:
        Success or error dict with new path
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return {"success": False, "error": "File not found"}

    parent   = os.path.dirname(path)
    new_path = os.path.join(parent, new_name)

    if os.path.exists(new_path):
        return {"success": False, "error": f"A file named '{new_name}' already exists"}

    try:
        os.rename(path, new_path)
        logger.info(f"Renamed: {path} → {new_path}")
        return {"success": True, "old_path": path, "new_path": new_path, "new_name": new_name}
    except Exception as e:
        logger.error(f"Rename failed: {e}")
        return {"success": False, "error": str(e)}


def move_file(path: str, destination: str) -> dict:
    """
    Move a file or folder to a new location.

    Args:
        path:        Full path to the file
        destination: Destination directory path

    Returns:
        Success or error dict
    """
    path        = os.path.expanduser(path)
    destination = os.path.expanduser(destination)

    if not os.path.exists(path):
        return {"success": False, "error": "Source file not found"}

    if not os.path.exists(destination):
        return {"success": False, "error": "Destination folder not found"}

    try:
        new_path = shutil.move(path, destination)
        logger.info(f"Moved: {path} → {new_path}")
        return {"success": True, "old_path": path, "new_path": new_path}
    except Exception as e:
        logger.error(f"Move failed: {e}")
        return {"success": False, "error": str(e)}


def delete_file(path: str, trash: bool = True) -> dict:
    """
    Delete a file or folder.
    By default moves to recycle bin (safe). Set trash=False for permanent delete.

    Args:
        path:  Full path to the file
        trash: If True, move to recycle bin instead of permanent delete

    Returns:
        Success or error dict
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return {"success": False, "error": "File not found"}

    try:
        if trash:
            # Use Windows shell to move to recycle bin
            import ctypes
            from ctypes import wintypes

            # SHFileOperation with FO_DELETE and FOF_ALLOWUNDO sends to recycle bin
            class SHFILEOPSTRUCT(ctypes.Structure):
                _fields_ = [
                    ("hwnd",                  wintypes.HWND),
                    ("wFunc",                 wintypes.UINT),
                    ("pFrom",                 wintypes.LPCWSTR),
                    ("pTo",                   wintypes.LPCWSTR),
                    ("fFlags",                ctypes.c_uint),
                    ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings",         ctypes.c_void_p),
                    ("lpszProgressTitle",     wintypes.LPCWSTR),
                ]

            FO_DELETE   = 0x0003
            FOF_ALLOWUNDO      = 0x0040
            FOF_NOCONFIRMATION = 0x0010
            FOF_SILENT         = 0x0004

            op = SHFILEOPSTRUCT()
            op.wFunc  = FO_DELETE
            op.pFrom  = path + "\0"
            op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

            result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
            if result == 0:
                logger.info(f"Sent to recycle bin: {path}")
                return {"success": True, "path": path, "method": "recycle_bin"}
            else:
                raise Exception(f"SHFileOperation returned {result}")
        else:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            logger.info(f"Permanently deleted: {path}")
            return {"success": True, "path": path, "method": "permanent"}

    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return {"success": False, "error": str(e)}


def create_folder(path: str) -> dict:
    """
    Create a new folder.

    Args:
        path: Full path of folder to create

    Returns:
        Success or error dict
    """
    path = os.path.expanduser(path)

    if os.path.exists(path):
        return {"success": False, "error": "Folder already exists"}

    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Created folder: {path}")
        return {"success": True, "path": path}
    except Exception as e:
        logger.error(f"Create folder failed: {e}")
        return {"success": False, "error": str(e)}


def get_file_info(path: str) -> dict:
    """Get detailed info about a file or folder."""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return {"error": "Path not found"}

    stat = os.stat(path)
    return {
        "name":      os.path.basename(path),
        "path":      path,
        "is_dir":    os.path.isdir(path),
        "size":      stat.st_size if not os.path.isdir(path) else 0,
        "size_str":  _format_size(stat.st_size),
        "modified":  stat.st_mtime,
        "type":      _get_file_type(path),
        "folder":    os.path.dirname(path),
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def _format_size(size_bytes: int) -> str:
    """Convert bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.1f} GB"


def _get_file_type(filename: str) -> str:
    """Return a friendly file type based on extension."""
    ext = Path(filename).suffix.lower()
    types = {
        # Documents
        ".pdf": "PDF", ".doc": "Word", ".docx": "Word",
        ".xls": "Excel", ".xlsx": "Excel",
        ".ppt": "PowerPoint", ".pptx": "PowerPoint",
        ".txt": "Text", ".md": "Markdown",
        # Code
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".html": "HTML", ".css": "CSS", ".json": "JSON",
        ".cpp": "C++", ".c": "C", ".java": "Java",
        # Images
        ".jpg": "Image", ".jpeg": "Image", ".png": "Image",
        ".gif": "GIF", ".svg": "SVG", ".webp": "Image",
        # Media
        ".mp4": "Video", ".mkv": "Video", ".avi": "Video",
        ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
        # Archives
        ".zip": "Archive", ".rar": "Archive", ".7z": "Archive",
        ".tar": "Archive", ".gz": "Archive",
        # Executables
        ".exe": "App", ".msi": "Installer", ".bat": "Script",
    }
    return types.get(ext, ext.lstrip(".").upper() if ext else "File")
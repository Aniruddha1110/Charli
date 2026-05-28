# charli.spec — PyInstaller build specification (faster-whisper, no torch)

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = []

# faster-whisper model files
try:
    datas += collect_data_files("faster_whisper")
except Exception:
    pass

# ctranslate2 (faster-whisper backend)
try:
    datas += collect_data_files("ctranslate2")
except Exception:
    pass

# tokenizers + huggingface
try:
    datas += collect_data_files("tokenizers")
    datas += collect_data_files("transformers")
except Exception:
    pass

# OpenWakeWord
try:
    datas += collect_data_files("openwakeword")
except Exception:
    pass

# pyttsx3
try:
    datas += collect_data_files("pyttsx3")
except Exception:
    pass

# LangChain
try:
    datas += collect_data_files("langchain")
    datas += collect_data_files("langchain_community")
except Exception:
    pass

hiddenimports = [
    # FastAPI + Uvicorn
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.main",
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic.deprecated.class_validators",

    # Audio
    "sounddevice",
    "scipy.io.wavfile",
    "scipy.signal",

    # faster-whisper
    "faster_whisper",
    "ctranslate2",
    "tokenizers",
    "huggingface_hub",

    # pyttsx3
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",

    # DB
    "sqlite3",

    # Automation
    "pyautogui",
    "pyperclip",
    "pycaw",
    "comtypes",
    "comtypes.client",
    "psutil",

    # Search
    "duckduckgo_search",
    "bs4",
    "requests",

    # Schedule + notifications
    "schedule",
    "plyer",
    "plyer.platforms.win.notification",

    # OpenWakeWord
    "openwakeword",
    "onnxruntime",

    # PIL
    "PIL",
    "PIL.ImageGrab",

    # LangChain
    "langchain",
    "langchain_community",
]

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchvision",
        "torchaudio",
        "tensorflow",
        "matplotlib",
        "tkinter",
        "PyQt5",
        "PyQt6",
        "wx",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "openai-whisper",
        "whisper",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="charli-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join("..", "assets", "icons", "charli.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="charli-backend",
)
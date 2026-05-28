@echo off
echo ╔══════════════════════════════════════╗
echo ║     Building Charli Desktop App      ║
echo ╚══════════════════════════════════════╝

:: ── Step 1: Activate venv ─────────────────────────────────────────────────
echo.
echo [1/4] Activating Python environment...
call venv\Scripts\activate.bat

:: ── Step 2: Build Python backend with PyInstaller ─────────────────────────
echo.
echo [2/4] Building Python backend (this takes 2-5 mins)...
cd python
pyinstaller charli.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller failed.
    pause
    exit /b 1
)
cd ..

:: ── Step 3: Copy backend into Electron resources ──────────────────────────
echo.
echo [3/4] Copying backend into Electron...
if not exist "electron\resources" mkdir electron\resources
xcopy /E /I /Y "python\dist\charli-backend" "electron\resources\charli-backend"

:: ── Step 4: Build Electron installer ──────────────────────────────────────
echo.
echo [4/4] Building Electron installer...
cd electron
npm run build
if %errorlevel% neq 0 (
    echo ERROR: Electron build failed.
    pause
    exit /b 1
)
cd ..

echo.
echo ╔══════════════════════════════════════╗
echo ║     Build complete!                  ║
echo ║     Check: electron\dist\           ║
echo ╚══════════════════════════════════════╝
pause
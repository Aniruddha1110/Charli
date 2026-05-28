// ── Imports ────────────────────────────────────────────────────────────────

const { app, BrowserWindow, ipcMain, Notification, globalShortcut, Tray, Menu, nativeImage } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

// ── Backend process management ─────────────────────────────────────────────

let backendProcess = null;

function startBackend() {
  if (app.isPackaged) {
    const backendPath = path.join(
      process.resourcesPath,
      "charli-backend",
      "charli-backend.exe"
    );

    console.log("Starting backend:", backendPath);

    backendProcess = spawn(backendPath, [], {
      detached: false,
      stdio: "ignore",
      windowsHide: true,
    });

    backendProcess.on("error", (err) => {
      console.error("Backend failed to start:", err);
    });

    backendProcess.on("exit", (code) => {
      console.log("Backend exited with code:", code);
    });

    console.log("Backend started, PID:", backendProcess.pid);
  }
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

// ── State ──────────────────────────────────────────────────────────────────

let mainWindow           = null;
let tray                 = null;
let wakeWordPollInterval = null;

// ── Create main window ─────────────────────────────────────────────────────

function createWindow() {
  const iconPath = path.join(__dirname, "../assets/icons/Charli.png");

  mainWindow = new BrowserWindow({
    width:    1100,
    height:   750,
    minWidth: 800,
    minHeight: 550,
    backgroundColor: "#0f0f0f",
    frame: false,
    icon:  iconPath,
    show:  false,
    webPreferences: {
      preload:          path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration:  false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "renderer/index.html"));

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("close", (e) => {
    if (!app._forceQuit) {
      e.preventDefault();
      mainWindow.hide();
      if (!app._trayNotified) {
        app._trayNotified = true;
        tray && tray.displayBalloon({
          iconType: "info",
          title:    "Charli is still running",
          content:  "Charli is minimised to the tray. Press Ctrl+Space to open.",
        });
      }
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── System tray ────────────────────────────────────────────────────────────

function createTray() {
  const trayIconPath = path.join(__dirname, "../assets/icons/tray.png");
  const icon         = nativeImage.createFromPath(trayIconPath);

  tray = new Tray(icon.resize({ width: 16, height: 16 }));
  tray.setToolTip("Charli — Desktop Copilot");

  updateTrayMenu();

  tray.on("click", () => {
    if (mainWindow && mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      activateCharli();
    }
  });

  tray.on("double-click", () => {
    activateCharli();
  });
}

function updateTrayMenu(isListening = false) {
  if (!tray) return;

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open Charli",
      icon:  nativeImage
               .createFromPath(path.join(__dirname, "../assets/icons/tray.png"))
               .resize({ width: 16, height: 16 }),
      click: () => activateCharli(),
    },
    { type: "separator" },
    {
      label: "New Chat",
      click: () => {
        activateCharli();
        if (mainWindow) mainWindow.webContents.send("tray-new-chat");
      },
    },
    {
      label: isListening ? "🔴 Listening..." : "Start Listening",
      click: () => {
        activateCharli();
        if (mainWindow) mainWindow.webContents.send("tray-start-voice");
      },
    },
    { type: "separator" },
    {
      label: "Settings",
      click: () => {
        activateCharli();
        if (mainWindow) mainWindow.webContents.send("tray-open-settings");
      },
    },
    { type: "separator" },
    {
      label: "Quit Charli",
      click: () => {
        app._forceQuit = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
}

// ── Activate Charli ────────────────────────────────────────────────────────

function activateCharli() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow();
    return;
  }

  if (mainWindow.isMinimized()) mainWindow.restore();
  if (!mainWindow.isVisible())  mainWindow.show();

  mainWindow.focus();
  mainWindow.setAlwaysOnTop(true);

  setTimeout(() => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.setAlwaysOnTop(false);
    }
  }, 200);
}

// ── Wake word polling ──────────────────────────────────────────────────────

function startWakeWordPolling() {
  wakeWordPollInterval = setInterval(() => {
    try {
      const request = net.request("http://127.0.0.1:8000/wake/triggered");

      request.on("response", (response) => {
        let data = "";
        response.on("data",  (chunk) => { data += chunk; });
        response.on("end",   () => {
          try {
            const json = JSON.parse(data);
            if (json.triggered) {
              activateCharli();
              if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send("wake-word-triggered");
              }
            }
          } catch {}
        });
      });

      request.on("error", () => {});
      request.end();
    } catch {}
  }, 1000);
}

// ── Wait for backend ───────────────────────────────────────────────────────

async function waitForBackend(maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = net.request("http://127.0.0.1:8000/");
        req.on("response", (res) => {
          if (res.statusCode === 200) resolve();
          else reject();
        });
        req.on("error", reject);
        req.end();
      });
      console.log("Backend is ready.");
      return true;
    } catch {
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  console.error("Backend did not start in time.");
  return false;
}

// ── Startup setting ────────────────────────────────────────────────────────

function applyStartupSetting(enabled) {
  app.setLoginItemSettings({
    openAtLogin: enabled,
    name:        "Charli",
    args:        ["--hidden"],
  });
}

// ── App lifecycle ──────────────────────────────────────────────────────────

const { net } = require("electron");

app.whenReady().then(async () => {
  startBackend();

  if (process.platform === "win32") {
    app.setAppUserModelId("com.aniruddha.charli");
  }

  if (app.isPackaged) {
    console.log("Waiting for backend to start...");
    await waitForBackend();
  }

  createWindow();
  createTray();

  const registered = globalShortcut.register("CommandOrControl+Space", () => {
    activateCharli();
  });

  if (registered) {
    console.log("Global hotkey Ctrl+Space registered.");
  } else {
    console.warn("Global hotkey registration failed.");
  }

  startWakeWordPolling();
});

app.on("before-quit", () => {
  stopBackend();
  app._forceQuit = true;
  globalShortcut.unregisterAll();
  if (wakeWordPollInterval) clearInterval(wakeWordPollInterval);
  if (tray) { tray.destroy(); tray = null; }
});

app.on("window-all-closed", () => {
  // Keep running in tray
});

app.on("activate", () => {
  if (!mainWindow || mainWindow.isDestroyed()) createWindow();
});

// ── IPC handlers ───────────────────────────────────────────────────────────

ipcMain.on("window-minimize", () => mainWindow?.minimize());
ipcMain.on("window-maximize", () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});
ipcMain.on("window-close",    () => mainWindow?.hide());
ipcMain.on("window-quit",     () => { app._forceQuit = true; app.quit(); });

ipcMain.on("show-notification", (_, { title, body }) => {
  new Notification({ title, body }).show();
});

ipcMain.on("activate-charli", () => activateCharli());

ipcMain.on("set-startup", (_, enabled) => {
  applyStartupSetting(enabled);
});

ipcMain.on("wake-word-start", (_, threshold) => {
  const req = net.request({ method: "POST", url: "http://127.0.0.1:8000/wake/" });
  req.setHeader("Content-Type", "application/json");
  req.on("response", () => {});
  req.on("error",    () => {});
  req.write(JSON.stringify({ enabled: true, threshold: threshold || 0.5 }));
  req.end();
});

ipcMain.on("wake-word-stop", () => {
  const req = net.request({ method: "POST", url: "http://127.0.0.1:8000/wake/" });
  req.setHeader("Content-Type", "application/json");
  req.on("response", () => {});
  req.on("error",    () => {});
  req.write(JSON.stringify({ enabled: false }));
  req.end();
});

ipcMain.handle("get-api-url", () => "http://127.0.0.1:8000");
const {
  app, BrowserWindow, ipcMain,
  Notification, globalShortcut,
  Tray, Menu, nativeImage
} = require("electron");
const path = require("path");

let mainWindow          = null;
let tray                = null;
let wakeWordPollInterval = null;


// ── Create main window ─────────────────────────────────────────────────────

function createWindow() {
  const iconPath = path.join(__dirname, "../assets/icons/Charli.png");

  mainWindow = new BrowserWindow({
    width:     1100,
    height:    750,
    minWidth:  800,
    minHeight: 550,
    backgroundColor: "#0f0f0f",
    frame: false,
    icon:  iconPath,
    show:  false,    // Don't show until ready
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration:  false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "renderer/index.html"));

  // Show window when ready to avoid white flash
  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  // Hide to tray instead of closing
  mainWindow.on("close", (e) => {
    if (!app._forceQuit) {
      e.preventDefault();
      mainWindow.hide();
      // Show tray notification first time
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

  // Single click → show/hide window
  tray.on("click", () => {
    if (mainWindow && mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      activateCharli();
    }
  });

  // Double click → always show
  tray.on("double-click", () => {
    activateCharli();
  });
}

function updateTrayMenu(isListening = false) {
  if (!tray) return;

  const contextMenu = Menu.buildFromTemplate([
    {
      label:   "Open Charli",
      icon:    nativeImage
                .createFromPath(path.join(__dirname, "../assets/icons/tray.png"))
                .resize({ width: 16, height: 16 }),
      click:   () => activateCharli(),
    },
    { type: "separator" },
    {
      label:   "New Chat",
      click:   () => {
        activateCharli();
        if (mainWindow) {
          mainWindow.webContents.send("tray-new-chat");
        }
      },
    },
    {
      label:   isListening ? "🔴 Listening..." : "Start Listening",
      click:   () => {
        activateCharli();
        if (mainWindow) {
          mainWindow.webContents.send("tray-start-voice");
        }
      },
    },
    { type: "separator" },
    {
      label:   "Settings",
      click:   () => {
        activateCharli();
        if (mainWindow) {
          mainWindow.webContents.send("tray-open-settings");
        }
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
      const { net } = require("electron");
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


// ── App lifecycle ──────────────────────────────────────────────────────────

app.whenReady().then(() => {
  if (process.platform === "win32") {
    app.setAppUserModelId("com.aniruddha.charli");
  }

  createWindow();
  createTray();

  // Global hotkey — Ctrl+Space opens Charli from anywhere
  const registered = globalShortcut.register("CommandOrControl+Space", () => {
    activateCharli();
  });

  if (registered) {
    console.log("Global hotkey Ctrl+Space registered.");
  } else {
    console.warn("Global hotkey registration failed — may be in use by another app.");
  }

  startWakeWordPolling();
});

app.on("before-quit", () => {
  app._forceQuit = true;
  globalShortcut.unregisterAll();
  if (wakeWordPollInterval) clearInterval(wakeWordPollInterval);
  if (tray) { tray.destroy(); tray = null; }
});

// Prevent app from quitting when all windows closed
app.on("window-all-closed", () => {
  // Keep running in tray — do NOT call app.quit()
});

app.on("activate", () => {
  if (!mainWindow || mainWindow.isDestroyed()) createWindow();
});


// ── Startup setting — launch on Windows boot ───────────────────────────────

function applyStartupSetting(enabled) {
  app.setLoginItemSettings({
    openAtLogin: enabled,
    name:        "Charli",
    args:        ["--hidden"],   // Start minimised to tray
  });
}


// ── IPC handlers ──────────────────────────────────────────────────────────

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
  const { net } = require("electron");
  const req     = net.request({ method: "POST", url: "http://127.0.0.1:8000/wake/" });
  req.setHeader("Content-Type", "application/json");
  req.on("response", () => {});
  req.on("error",    () => {});
  req.write(JSON.stringify({ enabled: true, threshold: threshold || 0.5 }));
  req.end();
});

ipcMain.on("wake-word-stop", () => {
  const { net } = require("electron");
  const req     = net.request({ method: "POST", url: "http://127.0.0.1:8000/wake/" });
  req.setHeader("Content-Type", "application/json");
  req.on("response", () => {});
  req.on("error",    () => {});
  req.write(JSON.stringify({ enabled: false }));
  req.end();
});

ipcMain.handle("get-api-url", () => "http://127.0.0.1:8000");
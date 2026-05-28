const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("charli", {
  minimize:      () => ipcRenderer.send("window-minimize"),
  maximize:      () => ipcRenderer.send("window-maximize"),
  close:         () => ipcRenderer.send("window-close"),
  quit:          () => ipcRenderer.send("window-quit"),
  notify:        (title, body) => ipcRenderer.send("show-notification", { title, body }),
  getApiUrl:     () => ipcRenderer.invoke("get-api-url"),
  setStartup:    (enabled) => ipcRenderer.send("set-startup", enabled),
  startWakeWord: (threshold) => ipcRenderer.send("wake-word-start", threshold),
  stopWakeWord:  () => ipcRenderer.send("wake-word-stop"),
  onWakeWord:    (cb) => ipcRenderer.on("wake-word-triggered", cb),
  onTrayNewChat:      (cb) => ipcRenderer.on("tray-new-chat",      cb),
  onTrayStartVoice:   (cb) => ipcRenderer.on("tray-start-voice",   cb),
  onTrayOpenSettings: (cb) => ipcRenderer.on("tray-open-settings", cb),
});
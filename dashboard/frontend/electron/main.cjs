/**
 * @header {
 *   "module": "electron-main",
 *   "layer": "desktop",
 *   "domain": "console",
 *   "description": "보안 격리된 BrowserWindow에서 OPAL Console renderer를 여는 Electron main",
 *   "exports": []
 * }
 */

const { app, BrowserWindow } = require("electron");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const CONSOLE_WINDOW_TITLE = "OPAL Console";

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 760,
    title: CONSOLE_WINDOW_TITLE,
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  const devUrl = process.env.OPAL_CONSOLE_DEV_URL;
  if (devUrl) {
    void window.loadURL(devUrl);
    return;
  }
  const indexUrl = pathToFileURL(path.join(__dirname, "../dist/index.html"));
  void window.loadURL(indexUrl.toString());
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });

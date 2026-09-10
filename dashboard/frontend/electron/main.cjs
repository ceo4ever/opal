/**
 * @header {
 *   "module": "electron-main",
 *   "layer": "desktop",
 *   "domain": "workbench",
 *   "description": "보안 격리된 BrowserWindow에서 Workbench renderer를 여는 Electron main",
 *   "exports": []
 * }
 */

const { app, BrowserWindow } = require("electron");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 760,
    title: "OPAL Product OS Workbench",
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  const devUrl = process.env.OPAL_WORKBENCH_DEV_URL;
  if (devUrl) {
    const url = new URL(devUrl);
    url.searchParams.set("workbench", "1");
    void window.loadURL(url.toString());
    return;
  }
  const indexUrl = pathToFileURL(path.join(__dirname, "../dist/index.html"));
  indexUrl.searchParams.set("workbench", "1");
  void window.loadURL(indexUrl.toString());
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });

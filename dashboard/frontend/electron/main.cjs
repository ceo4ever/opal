/**
 * @header {
 *   "module": "electron-main",
 *   "layer": "desktop",
 *   "domain": "workbench",
 *   "description": "보안 격리된 BrowserWindow에서 Workbench renderer를 열고 창 제목을 페이지 title 동기화로부터 고정하는 Electron main",
 *   "exports": []
 * }
 */

const { app, BrowserWindow } = require("electron");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const WORKBENCH_WINDOW_TITLE = "OPAL Product OS Workbench";

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 760,
    title: WORKBENCH_WINDOW_TITLE,
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  // index.html의 <title>OPAL Console</title>은 기존 Console 화면의 것이라 그대로 둔다(C-6).
  // Electron은 페이지 title이 로드되면 창 제목을 그 값으로 덮어쓰므로, Workbench shell을 여는
  // 이 main 프로세스에서는 그 동기화를 막고 창 제목을 Workbench 이름으로 고정한다.
  window.on("page-title-updated", (event) => { event.preventDefault(); });
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

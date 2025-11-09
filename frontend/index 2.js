const { app, BrowserWindow, Menu } = require("electron");

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 1300,
    height: 800,
    webPreferences: {
      nodeIntegration: true,  // script.js가 index.html에서 실행되도록 허용
    },
  });

  Menu.setApplicationMenu(null);

  win.loadFile("app.html");

  win.on("closed", () => {
    win = null;
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (win === null) {
    createWindow();
  }
});

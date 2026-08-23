const { app, BrowserWindow } = require('electron');
const net = require('net');
const fs = require('fs');
const path = require('path');

// The app was renamed from Yardstick to Joystick, which moved Electron's
// userData directory and with it the saved connection profiles in
// localStorage. If this install has no data yet but an old directory
// exists, adopt its storage once.
function migrateLegacyUserData() {
  const newDir = app.getPath('userData');
  const marker = path.join(newDir, 'Local Storage');
  if (fs.existsSync(marker)) return;
  const appData = app.getPath('appData');
  for (const legacy of ['yardstick-gui', 'Yardstick']) {
    const oldStorage = path.join(appData, legacy, 'Local Storage');
    if (fs.existsSync(oldStorage)) {
      fs.mkdirSync(newDir, { recursive: true });
      fs.cpSync(oldStorage, marker, { recursive: true });
      return;
    }
  }
}

let mainWindow;
let serverPort;

function findFreePort(startPort) {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.listen(startPort, '127.0.0.1', () => {
      const { port } = probe.address();
      probe.close(() => resolve(port));
    });
    probe.on('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(findFreePort(startPort + 1));
      } else {
        reject(err);
      }
    });
  });
}

async function startBackend() {
  const port = await findFreePort(3001);
  process.env.PORT = String(port);
  const { serverReady } = require('../server/index.js');
  await serverReady;
  return port;
}

function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    title: 'Joystick',
    backgroundColor: '#0f1117',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    autoHideMenuBar: true,
  });

  mainWindow.loadURL(`http://localhost:${port}`);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  migrateLegacyUserData();
  serverPort = await startBackend();
  createWindow(serverPort);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(serverPort);
    }
  });
});

// On macOS an app stays running when its last window closes and is brought back
// by clicking the dock icon -- that is what the 'activate' handler above is for.
// Quitting here unconditionally would make it unreachable and would also kill the
// in-process backend, so only quit on the platforms where that is the convention.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

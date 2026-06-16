const { app, BrowserWindow } = require('electron');
const net = require('net');

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
    title: 'Yardstick Benchmark',
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
  serverPort = await startBackend();
  createWindow(serverPort);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(serverPort);
    }
  });
});

app.on('window-all-closed', () => {
  app.quit();
});

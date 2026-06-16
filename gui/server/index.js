const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const path = require('path');

const { register: registerCloud } = require('./cloud');
const { sessions } = require('./session');
const { registerConnectionHandlers } = require('./handlers/connection');
const { registerExperimentHandlers } = require('./handlers/experiment');
const { registerResultsHandlers } = require('./handlers/results');

const app = express();
app.use(cors());
app.use(express.json());

const clientDist = path.join(__dirname, '..', 'client', 'dist');
app.use(express.static(clientDist));

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
});

registerCloud(io);

io.on('connection', (socket) => {
  console.log(`[ws] client connected: ${socket.id}`);
  registerConnectionHandlers(socket);
  registerExperimentHandlers(socket);
  registerResultsHandlers(socket);
  socket.on('disconnect', () => console.log(`[ws] client disconnected: ${socket.id}`));
});

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', activeSessions: sessions.size });
});

app.get('*', (_req, res) => {
  res.sendFile(path.join(clientDist, 'index.html'));
});

const PORT = process.env.PORT || 3001;
const serverReady = new Promise((resolve) => {
  server.listen(PORT, () => {
    console.log(`Yardstick GUI server running on http://localhost:${PORT}`);
    resolve(Number(PORT));
  });
});

module.exports = { server, serverReady };

const sessions = new Map();

function getSession(sessionId, socket) {
  const session = sessions.get(sessionId);
  if (!session && socket) {
    socket.emit('ssh:error', { message: 'No active session.' });
  }
  return session || null;
}

module.exports = { sessions, getSession };

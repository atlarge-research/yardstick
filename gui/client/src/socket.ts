import { io } from 'socket.io-client';
import type { Socket } from 'socket.io-client';

export function createSocket(): Socket {
  return io(window.location.origin, { autoConnect: false });
}

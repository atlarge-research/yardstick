import { createContext, useContext } from 'react';
import type { Socket } from 'socket.io-client';

const SocketContext = createContext<Socket | null>(null);
export const SocketProvider = SocketContext.Provider;

export function useSocket(): Socket {
  const s = useContext(SocketContext);
  if (!s) throw new Error('useSocket must be used within a SessionPane');
  return s;
}

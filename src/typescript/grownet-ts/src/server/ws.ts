import { FastifyInstance } from 'fastify';
import websocket from '@fastify/websocket';

interface Subscriber {
  send(data: string): void;
}

const subscribers: Array<Subscriber> = [];

export async function registerWebSocket(app: FastifyInstance) {
  await app.register(websocket);

  app.get('/ws', { websocket: true }, (connection) => {
    const socket = connection.socket as unknown as Subscriber & { on(event: string, cb: (...args: unknown[]) => void): void };
    subscribers.push(socket);
    socket.on('close', () => {
      const index = subscribers.indexOf(socket);
      if (index >= 0) subscribers.splice(index, 1);
    });
  });
}

export function broadcastFrame(frame: unknown): void {
  const payload = JSON.stringify({ type: 'frame', data: frame, timestamp: Date.now() });
  for (let i = 0; i < subscribers.length; i += 1) {
    try { subscribers[i].send(payload); } catch (_err) { /* ignore */ }
  }
}


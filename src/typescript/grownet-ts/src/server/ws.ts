import { FastifyInstance } from 'fastify';
import websocket from '@fastify/websocket';

interface Subscriber {
  send(data: string): void;
}

const subscribers: Array<Subscriber> = [];

export async function registerWebSocket(app: FastifyInstance) {
  await app.register(websocket);

  app.get('/ws', { websocket: true }, (connection) => {
    const ws = connection.socket as unknown as Subscriber & { on(event: string, cb: (...args: any[]) => void): void };
    subscribers.push(ws);
    ws.on('close', () => {
      const idx = subscribers.indexOf(ws);
      if (idx >= 0) subscribers.splice(idx, 1);
    });
  });
}

export function broadcastFrame(frame: unknown): void {
  const payload = JSON.stringify({ type: 'frame', data: frame, timestamp: Date.now() });
  for (let i = 0; i < subscribers.length; i += 1) {
    try { subscribers[i].send(payload); } catch (_err) { /* ignore */ }
  }
}


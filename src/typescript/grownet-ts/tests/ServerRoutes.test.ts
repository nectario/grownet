import { describe, it, expect } from 'vitest';
import { createServer } from '../src/server/Server.js';

describe('Server routes', () => {
  it('compute-spatial-metrics responds with metrics', async () => {
    const app = await createServer();
    const res = await app.inject({
      method: 'POST',
      url: '/api/v1/region/compute-spatial-metrics',
      payload: { image2d: [[0, 1, 0], [0, 0, 0]], preferOutput: false },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json() as Record<string, unknown>;
    expect(body.activePixels).toBe(1);
    await app.close();
  });

  it('tick-nd responds with metrics', async () => {
    const app = await createServer();
    const res = await app.inject({
      method: 'POST',
      url: '/api/v1/region/tick-nd',
      payload: { port: 'pixels', tensor: [[0, 1], [0, 0]] },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json() as Record<string, unknown>;
    expect(body.deliveredEvents).toBe(1);
    await app.close();
  });
});


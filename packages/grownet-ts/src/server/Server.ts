import fastify from 'fastify';
import pino from 'pino';
import { registerComputeSpatialMetricsRoute } from './routes/computeSpatialMetrics.js';
import { registerTickNdRoute } from './routes/tickNd.js';

export async function createServer() {
  const logger = pino({ level: process.env.LOG_LEVEL || 'info' });
  const app = fastify({ logger });
  registerComputeSpatialMetricsRoute(app);
  registerTickNdRoute(app);
  return app;
}

if (process.argv[1] && process.argv[1].endsWith('Server.js')) {
  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3333;
  const host = process.env.HOST || '0.0.0.0';
  createServer()
    .then((app) => app.listen({ port, host }))
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.error(err);
      process.exit(1);
    });
}


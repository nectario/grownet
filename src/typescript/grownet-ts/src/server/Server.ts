import fastify from 'fastify';
import pino from 'pino';
import { registerComputeSpatialMetricsRoute } from './routes/computeSpatialMetrics.js';
import { registerTickNdRoute } from './routes/tickNd.js';

export async function createServer() {
  const logger = pino({ level: process.env.LOG_LEVEL || 'info' });
  const app = fastify({
    logger,
    ajv: {
      customOptions: {
        removeAdditional: true,
        useDefaults: true,
        coerceTypes: true,
        allErrors: true,
        strict: true,
      },
    },
  });
  registerComputeSpatialMetricsRoute(app);
  registerTickNdRoute(app);
  return app;
}
import fastify from 'fastify';

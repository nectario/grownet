import fastify, { FastifyInstance } from 'fastify';
import pino from 'pino';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import { registerComputeSpatialMetricsRoute } from './routes/computeSpatialMetrics.js';
import { registerTickNdRoute } from './routes/tickNd.js';
import { registerWiringAndGrowthRoutes } from './routes/wiringGrowth.js';
import { WorkerPool } from '../pal/worker/Pool.js';
import { registerWebSocket } from './ws.js';

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
  await app.register(swagger, {
    openapi: {
      info: { title: 'GrowNet Server API', version: '0.1.0' },
      servers: [{ url: '/' }],
      components: {},
      paths: {},
    },
  });
  await app.register(swaggerUi, {
    routePrefix: '/docs',
  });
  const typedApp = app as unknown as FastifyInstance;
  await registerWebSocket(typedApp);
  registerComputeSpatialMetricsRoute(typedApp);
  registerTickNdRoute(typedApp);
  registerWiringAndGrowthRoutes(typedApp);
  app.addHook('onClose', async () => {
    if (WorkerPool.instance) await WorkerPool.instance.close();
  });
  return app;
}

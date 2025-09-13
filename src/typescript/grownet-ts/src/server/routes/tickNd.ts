import { FastifyInstance, FastifyPluginCallback } from 'fastify';
import { Region } from '../../Region.js';
import { ParallelOptions } from '../../pal/index.js';

export function registerTickNdRoute(server: FastifyInstance): void {
  const handler: FastifyPluginCallback = (instance, _opts, done) => {
    instance.post('/api/v1/region/tick-nd', async (request, reply) => {
      const body = request.body as {
        port: string;
        tensor: number[] | number[][] | number[][][];
        options?: ParallelOptions;
      };
      const region = new Region('server');
      const metrics = region.tickND(body.port, body.tensor, body.options);
      reply.send({
        deliveredEvents: metrics.getDeliveredEvents(),
        totalSlots: metrics.getTotalSlots(),
        totalSynapses: metrics.getTotalSynapses(),
        activePixels: metrics.getActivePixels(),
        centroidRow: metrics.getCentroidRow(),
        centroidCol: metrics.getCentroidCol(),
        bboxRowMin: metrics.getBboxRowMin(),
        bboxRowMax: metrics.getBboxRowMax(),
        bboxColMin: metrics.getBboxColMin(),
        bboxColMax: metrics.getBboxColMax(),
      });
    });
    done();
  };
  server.register(handler);
}
import { FastifyInstance, FastifyPluginCallback } from 'fastify';

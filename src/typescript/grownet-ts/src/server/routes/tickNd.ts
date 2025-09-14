import { FastifyInstance, FastifyPluginCallback, FastifyReply, FastifyRequest } from 'fastify';
import { Region } from '../../Region.js';
import { ParallelOptions } from '../../pal/index.js';
import { tickNdSchema } from '../schemas.js';

export function registerTickNdRoute(server: FastifyInstance): void {
  const handler: FastifyPluginCallback = (instance: FastifyInstance, _opts: unknown, done: () => void): void => {
    instance.post('/api/v1/region/tick-nd', { schema: tickNdSchema }, async (request: FastifyRequest, reply: FastifyReply) => {
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

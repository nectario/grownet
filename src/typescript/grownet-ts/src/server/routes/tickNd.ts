import { FastifyInstance, FastifyPluginCallback } from 'fastify';
import { Region } from '../../Region.js';
import { ParallelOptions } from '../../pal/index.js';
import { tickNdSchema } from '../schemas.js';

export function registerTickNdRoute(server: FastifyInstance): void {
  const handler: FastifyPluginCallback = (instance, _opts, done) => {
    instance.post('/api/v1/region/tick-nd', { schema: tickNdSchema }, async (request, reply) => {
      const body = request.body as {
        port: string;
        tensor: number[] | number[][] | number[][][];
        options?: ParallelOptions;
      };
      const region = new Region('server');
      const metrics = region.tickND(body.port, body.tensor, body.options);
      reply.send({
        delivered_events: metrics.getDeliveredEvents(),
        total_slots: metrics.getTotalSlots(),
        total_synapses: metrics.getTotalSynapses(),
        active_pixels: metrics.getActivePixels(),
        centroid_row: metrics.getCentroidRow(),
        centroid_col: metrics.getCentroidCol(),
        bbox_row_min: metrics.getBboxRowMin(),
        bbox_row_max: metrics.getBboxRowMax(),
        bbox_col_min: metrics.getBboxColMin(),
        bbox_col_max: metrics.getBboxColMax(),
      });
    });
    done();
  };
  server.register(handler);
}
import { FastifyInstance, FastifyPluginCallback } from 'fastify';

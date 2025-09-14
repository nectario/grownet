/* eslint-disable @typescript-eslint/naming-convention */
import { FastifyInstance, FastifyPluginCallback, FastifyReply, FastifyRequest } from 'fastify';
import { Region } from '../../Region.js';
import { computeSpatialMetricsSchema } from '../schemas.js';

export function registerComputeSpatialMetricsRoute(server: FastifyInstance): void {
  const handler: FastifyPluginCallback = (instance: FastifyInstance, _opts: unknown, done: () => void): void => {
    instance.post('/api/v1/region/compute-spatial-metrics', { schema: computeSpatialMetricsSchema }, async (request: FastifyRequest, reply: FastifyReply) => {
      const body = request.body as {
        image2d:
          | number[][]
          | Float64Array
          | { data: number[]; height: number; width: number };
        preferOutput?: boolean;
      };
      const preferOutput = body.preferOutput === true;
      const region = new Region('server');
      const imageCandidate = body.image2d as unknown;
      let metrics;
      if (
        typeof imageCandidate === 'object' &&
        imageCandidate !== null &&
        (imageCandidate as { data?: unknown }).data &&
        (imageCandidate as { height?: unknown }).height &&
        (imageCandidate as { width?: unknown }).width
      ) {
        const typed = imageCandidate as { data: number[]; height: number; width: number };
        const arr = new Float64Array(typed.data);
        metrics = region.computeSpatialMetrics({ data: arr, height: typed.height, width: typed.width }, preferOutput);
      } else {
        metrics = region.computeSpatialMetrics(body.image2d as number[][], preferOutput);
      }
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

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

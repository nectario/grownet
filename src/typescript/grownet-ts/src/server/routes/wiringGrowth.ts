import { FastifyInstance, FastifyPluginCallback } from 'fastify';
import { Region } from '../../Region.js';
import { addInputLayer2DSchema, addOutputLayer2DSchema, bindInputSchema, connectWindowedSchema, setGrowthPolicySchema } from '../schemas.js';

export function registerWiringAndGrowthRoutes(server: FastifyInstance): void {
  const plugin: FastifyPluginCallback = (instance, _opts, done) => {
    instance.post('/api/v1/region/add-input-layer-2d', { schema: addInputLayer2DSchema }, async (request, reply) => {
      const body = request.body as { height: number; width: number; gain: number; epsilonFire: number };
      const region = new Region('server');
      const id = region.addInputLayer2D(body.height, body.width, body.gain, body.epsilonFire);
      reply.send({ layer_id: id });
    });

    instance.post('/api/v1/region/add-output-layer-2d', { schema: addOutputLayer2DSchema }, async (request, reply) => {
      const body = request.body as { height: number; width: number; smoothing: number };
      const region = new Region('server');
      const id = region.addOutputLayer2D(body.height, body.width, body.smoothing);
      reply.send({ layer_id: id });
    });

    instance.post('/api/v1/region/bind-input', { schema: bindInputSchema }, async (request, reply) => {
      const body = request.body as { port: string; layers: number[] };
      const region = new Region('server');
      region.bindInput(body.port, body.layers);
      reply.send({ ok: true });
    });

    instance.post('/api/v1/region/connect-windowed', { schema: connectWindowedSchema }, async (request, reply) => {
      const body = request.body as { src: number; dst: number; kernelH: number; kernelW: number; strideH: number; strideW: number; padding: string; feedback: boolean };
      const region = new Region('server');
      const unique = region.connectLayersWindowed(body.src, body.dst, body.kernelH, body.kernelW, body.strideH, body.strideW, body.padding, body.feedback);
      reply.send({ unique_sources: unique });
    });

    instance.post('/api/v1/region/set-growth-policy', { schema: setGrowthPolicySchema }, async (request, reply) => {
      const body = request.body as { enableLayerGrowth: boolean; maxLayers: number; avgSlotsThreshold: number; percentNeuronsAtCapacityThreshold?: number; layerCooldownTicks: number; rngSeed: number };
      const region = new Region('server');
      region.setGrowthPolicy(body);
      reply.send({ ok: true });
    });

    done();
  };
  server.register(plugin);
}


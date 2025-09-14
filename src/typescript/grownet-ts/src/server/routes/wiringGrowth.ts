import { FastifyInstance, FastifyPluginCallback } from 'fastify';
import { Region } from '../../Region.js';
import { addInputLayer2DSchema, addOutputLayer2DSchema, bindInputSchema, connectWindowedSchema, setGrowthPolicySchema, createRegionSchema, destroyRegionSchema, getRegionStateSchema, getMeshRulesSchema, connectTopographicSchema, requestLayerGrowthSchema } from '../schemas.js';
import { RegionRegistry } from '../sim/Registry.js';
import { connectLayersTopographic } from '../../wiring/TopographicWiring.js';
import type { TopographicConfig } from '../../wiring/TopographicWiring.js';

export function registerWiringAndGrowthRoutes(server: FastifyInstance): void {
  const plugin: FastifyPluginCallback = (instance, _opts, done) => {
    // Region lifecycle (optional long-lived sessions)
    instance.post('/api/v1/region/create', { schema: createRegionSchema }, async (request, reply) => {
      const body = request.body as { name?: string };
      const { regionId } = RegionRegistry.instance.create(body?.name);
      reply.send({ regionId });
    });
    instance.post('/api/v1/region/destroy', { schema: destroyRegionSchema }, async (request, reply) => {
      const body = request.body as { regionId: string };
      const successFlag = RegionRegistry.instance.destroy(body.regionId);
      reply.send({ success: successFlag });
    });
    instance.post('/api/v1/region/get-region-state', { schema: getRegionStateSchema }, async (request, reply) => {
      const body = request.body as { regionId: string };
      const region = RegionRegistry.instance.get(body.regionId);
      if (!region) { reply.code(404).send({ error: 'not_found' }); return; }
      const layers = region.getLayers();
      const busStep = layers[0]?.getBus().getCurrentStep?.() ?? 0;
      reply.send({ layersCount: layers.length, busStep });
    });

    instance.post('/api/v1/region/add-input-layer-2d', { schema: addInputLayer2DSchema }, async (request, reply) => {
      const body = request.body as { regionId?: string; height: number; width: number; gain: number; epsilonFire: number };
      const region = body.regionId ? (RegionRegistry.instance.get(body.regionId) ?? new Region('server')) : new Region('server');
      const layerId = region.addInputLayer2D(body.height, body.width, body.gain, body.epsilonFire);
      reply.send({ layerId });
    });

    instance.post('/api/v1/region/add-output-layer-2d', { schema: addOutputLayer2DSchema }, async (request, reply) => {
      const body = request.body as { regionId?: string; height: number; width: number; smoothing: number };
      const region = body.regionId ? (RegionRegistry.instance.get(body.regionId) ?? new Region('server')) : new Region('server');
      const layerId = region.addOutputLayer2D(body.height, body.width, body.smoothing);
      reply.send({ layerId });
    });

    instance.post('/api/v1/region/bind-input', { schema: bindInputSchema }, async (request, reply) => {
      const body = request.body as { regionId?: string; port: string; layers: number[] };
      const region = body.regionId ? (RegionRegistry.instance.get(body.regionId) ?? new Region('server')) : new Region('server');
      region.bindInput(body.port, body.layers);
      reply.send({ success: true });
    });

    instance.post('/api/v1/region/connect-windowed', { schema: connectWindowedSchema }, async (request, reply) => {
      const body = request.body as { regionId?: string; src: number; dst: number; kernelH: number; kernelW: number; strideH: number; strideW: number; padding: string; feedback: boolean };
      const region = body.regionId ? (RegionRegistry.instance.get(body.regionId) ?? new Region('server')) : new Region('server');
      const uniqueSources = region.connectLayersWindowed(body.src, body.dst, body.kernelH, body.kernelW, body.strideH, body.strideW, body.padding, body.feedback);
      reply.send({ uniqueSources });
    });

    instance.post('/api/v1/region/set-growth-policy', { schema: setGrowthPolicySchema }, async (request, reply) => {
      const body = request.body as { regionId?: string; enableLayerGrowth: boolean; maxLayers: number; avgSlotsThreshold: number; percentNeuronsAtCapacityThreshold?: number; layerCooldownTicks: number; rngSeed: number };
      const region = body.regionId ? (RegionRegistry.instance.get(body.regionId) ?? new Region('server')) : new Region('server');
      region.setGrowthPolicy(body);
      reply.send({ success: true });
    });

    // Topographic preset helper (pure geometry/weights)
    instance.post('/api/v1/region/connect-topographic', { schema: connectTopographicSchema }, async (request, reply) => {
      const body = request.body as { srcHeight: number; srcWidth: number; dstHeight: number; dstWidth: number; config: unknown };
      // Narrow config to the helper's type instead of any
      const res = connectLayersTopographic(body.srcHeight, body.srcWidth, body.dstHeight, body.dstWidth, body.config as TopographicConfig);
      reply.send({ uniqueSources: res.uniqueSources });
    });

    // Mesh inspection (ephemeral: will be empty unless a persistent region is used)
    instance.post('/api/v1/region/get-mesh-rules', { schema: getMeshRulesSchema }, async (request, reply) => {
      const body = request.body as { regionId?: string };
      const region = body.regionId ? RegionRegistry.instance.get(body.regionId) : undefined;
      const meshRules = region ? region.getMeshRules() : [];
      reply.send({ meshRules });
    });

    // Request spillover growth for a saturated layer (p=1.0 by default)
    instance.post('/api/v1/region/request-layer-growth', { schema: requestLayerGrowthSchema }, async (request, reply) => {
      const body = request.body as { regionId?: string; saturatedLayerIndex: number; connectionProbability?: number };
      const region = body.regionId ? (RegionRegistry.instance.get(body.regionId) ?? new Region('server')) : new Region('server');
      const newIndex = region.requestLayerGrowth(body.saturatedLayerIndex, body.connectionProbability ?? 1.0);
      reply.send({ newLayerIndex: newIndex });
    });

    done();
  };
  server.register(plugin);
}

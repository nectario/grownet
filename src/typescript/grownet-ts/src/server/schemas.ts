/* eslint-disable @typescript-eslint/naming-convention */
export const computeSpatialMetricsSchema = {
  body: {
    type: 'object',
    additionalProperties: false,
    required: ['image2d'],
    properties: {
      image2d: {
        oneOf: [
          {
            type: 'array',
            items: { type: 'array', items: { type: 'number' } },
          },
          {
            type: 'object',
            additionalProperties: false,
            required: ['data', 'height', 'width'],
            properties: {
              data: { type: 'array', items: { type: 'number' } },
              height: { type: 'integer', minimum: 0 },
              width: { type: 'integer', minimum: 0 },
            },
          },
        ],
      },
      preferOutput: { type: 'boolean' },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: {
      type: 'object',
      additionalProperties: false,
      properties: {
        delivered_events: { type: 'integer' },
        total_slots: { type: 'integer' },
        total_synapses: { type: 'integer' },
        active_pixels: { type: 'integer' },
        centroid_row: { type: 'number' },
        centroid_col: { type: 'number' },
        bbox_row_min: { type: 'integer' },
        bbox_row_max: { type: 'integer' },
        bbox_col_min: { type: 'integer' },
        bbox_col_max: { type: 'integer' },
      },
    },
  },
};

export const tickNdSchema = {
  body: {
    type: 'object',
    additionalProperties: false,
    required: ['port', 'tensor'],
    properties: {
      port: { type: 'string', minLength: 1 },
      tensor: {
        // nested arrays of numbers up to 3 levels
        anyOf: [
          { type: 'array', items: { type: 'number' } },
          { type: 'array', items: { type: 'array', items: { type: 'number' } } },
          {
            type: 'array',
            items: { type: 'array', items: { type: 'array', items: { type: 'number' } } },
          },
        ],
      },
      options: {
        type: 'object',
        additionalProperties: false,
        properties: {
          maxWorkers: { type: 'integer', minimum: 0 },
          tileSize: { type: 'integer', minimum: 1 },
          device: { enum: ['cpu', 'gpu', 'auto'] },
          vectorizationEnabled: { type: 'boolean' },
          reduction: { enum: ['ordered', 'pairwiseTree'] },
        },
      },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: {
      type: 'object',
      additionalProperties: false,
      properties: {
        delivered_events: { type: 'integer' },
        total_slots: { type: 'integer' },
        total_synapses: { type: 'integer' },
        active_pixels: { type: 'integer' },
        centroid_row: { type: 'number' },
        centroid_col: { type: 'number' },
        bbox_row_min: { type: 'integer' },
        bbox_row_max: { type: 'integer' },
        bbox_col_min: { type: 'integer' },
        bbox_col_max: { type: 'integer' },
      },
    },
  },
};

export const addInputLayer2DSchema = {
  body: {
    type: 'object',
    required: ['height', 'width', 'gain', 'epsilonFire'],
    additionalProperties: false,
    properties: {
      regionId: { type: 'string', nullable: true },
      height: { type: 'integer', minimum: 1 },
      width: { type: 'integer', minimum: 1 },
      gain: { type: 'number' },
      epsilonFire: { type: 'number' },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: { type: 'object', properties: { layerId: { type: 'integer' } }, additionalProperties: false },
  },
};

export const addOutputLayer2DSchema = {
  body: {
    type: 'object',
    required: ['height', 'width', 'smoothing'],
    additionalProperties: false,
    properties: {
      regionId: { type: 'string', nullable: true },
      height: { type: 'integer', minimum: 1 },
      width: { type: 'integer', minimum: 1 },
      smoothing: { type: 'number' },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: { type: 'object', properties: { layerId: { type: 'integer' } }, additionalProperties: false },
  },
};

export const bindInputSchema = {
  body: {
    type: 'object',
    required: ['port', 'layers'],
    additionalProperties: false,
    properties: {
      regionId: { type: 'string', nullable: true },
      port: { type: 'string' },
      layers: { type: 'array', items: { type: 'integer' } },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: { type: 'object', properties: { success: { type: 'boolean' } }, additionalProperties: false },
  },
};

export const connectWindowedSchema = {
  body: {
    type: 'object',
    required: ['src', 'dst', 'kernelH', 'kernelW', 'strideH', 'strideW', 'padding', 'feedback'],
    additionalProperties: false,
    properties: {
      regionId: { type: 'string', nullable: true },
      src: { type: 'integer', minimum: 0 },
      dst: { type: 'integer', minimum: 0 },
      kernelH: { type: 'integer', minimum: 1 },
      kernelW: { type: 'integer', minimum: 1 },
      strideH: { type: 'integer', minimum: 1 },
      strideW: { type: 'integer', minimum: 1 },
      padding: { enum: ['same', 'valid'] },
      feedback: { type: 'boolean' },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: { type: 'object', properties: { uniqueSources: { type: 'integer' } }, additionalProperties: false },
  },
};

export const setGrowthPolicySchema = {
  body: {
    type: 'object',
    required: ['enableLayerGrowth', 'maxLayers', 'avgSlotsThreshold', 'layerCooldownTicks', 'rngSeed'],
    additionalProperties: false,
    properties: {
      regionId: { type: 'string', nullable: true },
      enableLayerGrowth: { type: 'boolean' },
      maxLayers: { type: 'integer', minimum: 0 },
      avgSlotsThreshold: { type: 'number', minimum: 0 },
      percentNeuronsAtCapacityThreshold: { type: 'number' },
      layerCooldownTicks: { type: 'integer', minimum: 0 },
      rngSeed: { type: 'integer' },
    },
  },
  response: {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    200: { type: 'object', properties: { success: { type: 'boolean' } }, additionalProperties: false },
  },
};

export const createRegionSchema = {
  body: { type: 'object', additionalProperties: false, properties: { name: { type: 'string' } } },
  response: { 200: { type: 'object', additionalProperties: false, properties: { regionId: { type: 'string' } } } },
};

export const destroyRegionSchema = {
  body: { type: 'object', required: ['regionId'], additionalProperties: false, properties: { regionId: { type: 'string' } } },
  response: { 200: { type: 'object', additionalProperties: false, properties: { success: { type: 'boolean' } } } },
};

export const getRegionStateSchema = {
  body: { type: 'object', required: ['regionId'], additionalProperties: false, properties: { regionId: { type: 'string' } } },
  response: { 200: { type: 'object', additionalProperties: false, properties: { layersCount: { type: 'integer' }, busStep: { type: 'integer' } } } },
};

export const getMeshRulesSchema = {
  body: { type: 'object', additionalProperties: false, properties: { regionId: { type: 'string' } } },
  response: { 200: { type: 'object', additionalProperties: false, properties: { meshRules: { type: 'array', items: { type: 'object' } } } } },
};

export const connectTopographicSchema = {
  body: {
    type: 'object',
    required: ['srcHeight', 'srcWidth', 'dstHeight', 'dstWidth', 'config'],
    additionalProperties: false,
    properties: {
      srcHeight: { type: 'integer', minimum: 1 },
      srcWidth: { type: 'integer', minimum: 1 },
      dstHeight: { type: 'integer', minimum: 1 },
      dstWidth: { type: 'integer', minimum: 1 },
      config: { type: 'object' },
    },
  },
  response: { 200: { type: 'object', additionalProperties: false, properties: { uniqueSources: { type: 'integer' } } } },
};

export const requestLayerGrowthSchema = {
  body: {
    type: 'object', required: ['saturatedLayerIndex'], additionalProperties: false,
    properties: { regionId: { type: 'string' }, saturatedLayerIndex: { type: 'integer', minimum: 0 }, connectionProbability: { type: 'number' } },
  },
  response: { 200: { type: 'object', additionalProperties: false, properties: { newLayerIndex: { type: 'integer' } } } },
};

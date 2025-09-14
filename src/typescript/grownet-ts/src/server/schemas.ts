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
        deliveredEvents: { type: 'integer' },
        totalSlots: { type: 'integer' },
        totalSynapses: { type: 'integer' },
        activePixels: { type: 'integer' },
        centroidRow: { type: 'number' },
        centroidCol: { type: 'number' },
        bboxRowMin: { type: 'integer' },
        bboxRowMax: { type: 'integer' },
        bboxColMin: { type: 'integer' },
        bboxColMax: { type: 'integer' },
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
        deliveredEvents: { type: 'integer' },
        totalSlots: { type: 'integer' },
        totalSynapses: { type: 'integer' },
        activePixels: { type: 'integer' },
        centroidRow: { type: 'number' },
        centroidCol: { type: 'number' },
        bboxRowMin: { type: 'integer' },
        bboxRowMax: { type: 'integer' },
        bboxColMin: { type: 'integer' },
        bboxColMax: { type: 'integer' },
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

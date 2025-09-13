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


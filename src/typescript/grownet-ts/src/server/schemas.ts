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

import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('Spatial metrics parity', () => {
  it('bbox uses only active pixels and synapse count is positive after connect', () => {
    const region = new Region('spatial-metrics');
    const inId = region.addInputLayer2D(3, 3, 1.0, 0.01);
    const outId = region.addOutputLayer2D(3, 3, 0.0);
    // Connect center window 3x3 SAME
    region.connectLayersWindowed(inId, outId, 3, 3, 1, 1, 'same', false);

    // Two active pixels
    const metrics = region.computeSpatialMetrics({ data: new Float64Array([
      0, 1, 0,
      0, 0, 0,
      0, 0, 1,
    ]), height: 3, width: 3 }, false);
    expect(metrics.getBboxRowMin()).toBe(0);
    expect(metrics.getBboxColMin()).toBe(1);
    expect(metrics.getBboxRowMax()).toBe(2);
    expect(metrics.getBboxColMax()).toBe(2);

    // After connect, total synapses should be > 0
    expect(metrics.getTotalSynapses()).toBeGreaterThan(0);
  });
});


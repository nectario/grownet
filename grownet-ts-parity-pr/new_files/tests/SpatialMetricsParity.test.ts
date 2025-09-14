import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

// Verifies bbox only considers positive pixels and synapse counting is non-zero after connections.
describe('Spatial metrics parity', () => {
  it('updates bbox only for active pixels and reports synapse count', () => {
    const region = new Region('ts-spatial-metrics');
    const layerZeroIndex = region.addLayer(2, 0, 0);
    const layerOneIndex = region.addLayer(2, 0, 0);
    region.connectLayers(layerZeroIndex, layerOneIndex, 1.0, false);

    const image = [
      [0, 0, 0],
      [0, 1, 0],
      [0, 0, 2],
    ];
    const metrics = region.computeSpatialMetrics(image, true);
    expect(metrics.activePixels).toBe(2);
    expect(metrics.bboxRowMin).toBe(1);
    expect(metrics.bboxColMin).toBe(1);
    expect(metrics.bboxRowMax).toBe(2);
    expect(metrics.bboxColMax).toBe(2);
    expect(metrics.totalSynapses).toBeGreaterThan(0);
  });
});

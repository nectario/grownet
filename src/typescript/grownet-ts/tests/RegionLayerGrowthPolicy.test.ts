import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('Region layer growth policy', () => {
  it('Adds at most one layer per tick when triggers pass', () => {
    const region = new Region('policy-growth');
    const inId = region.addInputLayer2D(2, 2, 1.0, 0.01);
    const hidId = region.addLayer(1);
    region.bindInput('p', [inId]);
    region.setGrowthPolicy({ enableLayerGrowth: true, maxLayers: 64, avgSlotsThreshold: 0.0, layerCooldownTicks: 0, rngSeed: 1234 });

    let prevLayers = (region as unknown as { layers: Array<unknown> }).layers.length;
    for (let tickIndex = 0; tickIndex < 3; tickIndex += 1) {
      const metrics = region.tickND('p', [[1, 0], [0, 0]]);
      expect(metrics.getDeliveredEvents()).toBeGreaterThanOrEqual(1);
      const nowLayers = (region as unknown as { layers: Array<unknown> }).layers.length;
      const delta = nowLayers - prevLayers;
      expect(delta === 0 || delta === 1).toBe(true);
      prevLayers = nowLayers;
    }
  });
});


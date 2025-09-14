import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('Auto neuron growth (fallback streak + cooldown)', () => {
  it('grows at most one neuron per layer per tick', () => {
    const region = new Region('auto-growth');
    const inputId = region.addInputLayer2D(2, 2, 1.0, 0.01);
    const hiddenId = region.addLayer(1);
    region.bindInput('pixels', [inputId]);

    // Configure slot policy to trigger growth quickly
    const hiddenLayer = (region as unknown as { getLayers: () => Array<any> }).getLayers()[hiddenId];
    const neurons = hiddenLayer.getNeurons();
    for (const neuron of neurons) {
      (neuron as unknown as { setSlotLimit?: (n: number) => void }).setSlotLimit?.(1);
      // fallbackGrowthThreshold = 1 for rapid trigger; cooldown = 0
      const cfg = (neuron as unknown as { config?: { fallbackGrowthThreshold?: number; neuronGrowthCooldownTicks?: number } }).config;
      if (cfg) {
        cfg.fallbackGrowthThreshold = 1;
        cfg.neuronGrowthCooldownTicks = 0;
      }
    }

    const before = hiddenLayer.getNeurons().length;
    // Drive a value that causes fallback at capacity to build streak
    region.tickND('pixels', [[1, 0], [0, 0]]);
    const after = hiddenLayer.getNeurons().length;
    expect(after).toBeGreaterThanOrEqual(before);
    // And never more than one per tick per layer
    expect(after - before <= 1).toBe(true);
  });
});


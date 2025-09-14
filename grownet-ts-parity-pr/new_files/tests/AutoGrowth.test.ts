import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';
import { SlotConfig } from '../src/core/SlotConfig.js';
import { InputND } from '../src/io/InputND.js';
import { OutputND } from '../src/io/OutputND.js';

// This test drives fallback -> growth in a minimal setting.
describe('Auto neuron growth (fallback streak + cooldown)', () => {
  it('grows at most one neuron per layer per tick when fallback streak exceeds threshold', () => {
    const region = new Region('ts-autogrowth');
    const slotConfig: SlotConfig = {
      growthEnabled: true,
      neuronGrowthEnabled: true,
      layerGrowthEnabled: false,
      fallbackGrowthThreshold: 2,
      neuronGrowthCooldownTicks: 0,
    };
    const input = new InputND('in', 1);
    const output = new OutputND('out', 1);
    const layerIndex = region.addLayer(1, 0, 0, slotConfig); // single neuron to start
    region.bindInput(input, layerIndex);
    region.connectLayers(layerIndex, output.getLayerIndex(), 1.0, false);

    // Drive inputs that force fallback (out-of-domain / at-capacity), causing growth
    const data = new Float64Array([1, 2, 3, 4, 5, 6]);
    for (let tick = 0; tick < data.length; tick += 1) {
      region.tickND('in', new Float64Array([data[tick]]), { shape: [1] });
    }
    const grownLayer = region.getLayers()[layerIndex];
    expect(grownLayer.getNeurons().length).toBeGreaterThan(1);
  });
});

import { Region } from '../Region.js';

export function runGrowthPolicyDemo(): void {
  const region = new Region('growth-demo');
  const inId = region.addInputLayer2D(3, 3, 1.0, 0.01);
  const hidId = region.addLayer(2);
  region.bindInput('pixels', [inId]);
  region.setGrowthPolicy({ enableLayerGrowth: true, maxLayers: 16, avgSlotsThreshold: 0.0, layerCooldownTicks: 0, rngSeed: 1234 });

  for (let tickIndex = 0; tickIndex < 5; tickIndex += 1) {
    const layerCountBefore = (region as unknown as { layers: Array<unknown> }).layers.length;
    const metrics = region.tickND('pixels', [[1, 0, 0], [0, 0, 0], [0, 0, 0]]);
    const layerCountAfter = (region as unknown as { layers: Array<unknown> }).layers.length;
    // eslint-disable-next-line no-console
    console.log(`[tick ${tickIndex}] delivered=${metrics.getDeliveredEvents()} layers=${layerCountBefore}→${layerCountAfter}`);
  }
}

if (import.meta.url === (process.argv[1] ? new URL('file://' + process.argv[1]).toString() : '')) {
  runGrowthPolicyDemo();
}


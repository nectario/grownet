import { describe, it, expect } from 'vitest';
import { connectLayersTopographic, defaultTopographicConfig } from '../src/wiring/TopographicWiring.js';

describe('Topographic preset', () => {
  it('Gaussian weights normalize per center', () => {
    const cfg = defaultTopographicConfig();
    cfg.kernelH = 3; cfg.kernelW = 3; cfg.strideH = 1; cfg.strideW = 1; cfg.padding = 'valid';
    const res = connectLayersTopographic(5, 5, 5, 5, cfg);
    expect(res.uniqueSources).toBe(25);
    // Each window (center) should have weights summing to ~1
    for (let i = 0; i < res.incomingPerCenter.length; i += 1) {
      let sum = 0;
      for (let j = 0; j < res.incomingPerCenter[i].weights.length; j += 1) sum += res.incomingPerCenter[i].weights[j].weight;
      expect(sum).toBeCloseTo(1.0, 9);
    }
  });
});

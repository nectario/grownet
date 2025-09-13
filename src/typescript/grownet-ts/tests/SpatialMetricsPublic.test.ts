import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('SpatialMetrics public', () => {
  it('FromImage', () => {
    const region = new Region('spatial-metrics');
    const img = [ [0.0, 1.0, 0.0], [0.0, 0.0, 0.0] ];
    const m = region.computeSpatialMetrics(img, false);
    expect(m.getActivePixels()).toBe(1);
    expect(m.getCentroidRow()).toBeCloseTo(0.0, 12);
    expect(m.getCentroidCol()).toBeCloseTo(1.0, 12);
    expect(m.getBboxRowMin()).toBe(0);
    expect(m.getBboxRowMax()).toBe(0);
    expect(m.getBboxColMin()).toBe(1);
    expect(m.getBboxColMax()).toBe(1);
  });
});
import { describe, it, expect } from 'vitest';

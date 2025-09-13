import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('SpatialMetrics public', () => {
  it('FromImage', () => {
    const region = new Region('spatial-metrics');
    const image = [ [0.0, 1.0, 0.0], [0.0, 0.0, 0.0] ];
    const metrics = region.computeSpatialMetrics(image, false);
    expect(metrics.getActivePixels()).toBe(1);
    expect(metrics.getCentroidRow()).toBeCloseTo(0.0, 12);
    expect(metrics.getCentroidCol()).toBeCloseTo(1.0, 12);
    expect(metrics.getBboxRowMin()).toBe(0);
    expect(metrics.getBboxRowMax()).toBe(0);
    expect(metrics.getBboxColMin()).toBe(1);
    expect(metrics.getBboxColMax()).toBe(1);
  });
});
import { describe, it, expect } from 'vitest';

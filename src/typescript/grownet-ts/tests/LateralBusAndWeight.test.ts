import { describe, it, expect } from 'vitest';
import { LateralBus } from '../src/core/LateralBus.js';
import { Weight } from '../src/core/Weight.js';

describe('LateralBus decay and Weight freeze', () => {
  it('Bus.decay applies invariants', () => {
    const bus = new LateralBus(0.9);
    bus.setInhibitionFactor(0.7);
    bus.setModulationFactor(1.5);
    bus.decay();
    expect(bus.getInhibitionFactor()).toBeCloseTo(0.63, 12);
    expect(bus.getModulationFactor()).toBeCloseTo(1.0, 12);
    expect(bus.getCurrentStep()).toBe(1);
  });

  it('Weight.freeze prevents updates, unfreeze resumes', () => {
    const w = new Weight();
    const t0 = w.getThreshold();
    w.reinforce(2.0);
    const s1 = w.getStrength();
    w.freeze();
    w.reinforce(2.0);
    expect(w.getStrength()).toBeCloseTo(s1, 12);
    const firedBefore = w.updateThreshold(0.0);
    const t1 = w.getThreshold();
    w.unfreeze();
    const firedAfter = w.updateThreshold(1.0);
    const t2 = w.getThreshold();
    expect(t1).toBeCloseTo(t0, 12);
    expect(firedBefore).toBe(false);
    expect(firedAfter).toBe(true);
    expect(t2).toBeGreaterThan(t1);
  });
});


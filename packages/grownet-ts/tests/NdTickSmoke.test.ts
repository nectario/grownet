import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('ND Tick smoke', () => {
  it('counts delivered events for simple tensor', () => {
    const region = new Region('nd-smoke');
    const tensor = [ [0, 0, 0], [0, 1, 0] ];
    const m = region.tickND('pixels', tensor);
    expect(m.getDeliveredEvents()).toBe(1);
    expect(m.getTotalSlots()).toBe(6);
  });
});


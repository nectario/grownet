import { describe, it, expect } from 'vitest';
import { parallelMap, counterRng, ParallelOptions } from '../src/pal/index.js';

class RangeDomain {
  private n: number;
  constructor(n: number) { this.n = n; }
  size(): number { return this.n; }
  at(index: number): number { return index; }
}

describe('PAL determinism', () => {
  it('ordered reduction identical across worker counts', async () => {
    const N = 10000;
    const domain = new RangeDomain(N);
    const kernel = (i: number) => counterRng(1234, 0, 1, 0, i, 0);
    const reduceInOrder = (vals: number[]) => vals.reduce((a, b) => a + b, 0);

    const opt1: ParallelOptions = { maxWorkers: 1 };
    const opt2: ParallelOptions = { maxWorkers: 8 };
    const a = await parallelMap(domain, kernel, reduceInOrder, opt1);
    const b = await parallelMap(domain, kernel, reduceInOrder, opt2);
    expect(a).toBeCloseTo(b, 12);
  });
});
import { describe, it, expect } from 'vitest';

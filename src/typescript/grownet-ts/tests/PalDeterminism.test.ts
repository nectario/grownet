import { describe, it, expect } from 'vitest';
import { parallelMap, counterRng, ParallelOptions } from '../src/pal/index.js';

class RangeDomain {
  private itemCount: number;
  constructor(itemCount: number) { this.itemCount = itemCount; }
  size(): number { return this.itemCount; }
  at(index: number): number { return index; }
}

describe('PAL determinism', () => {
  it('ordered reduction identical across worker counts', async () => {
    const sampleCount = 10000;
    const domain = new RangeDomain(sampleCount);
    const kernel = (indexValue: number) => counterRng(1234, 0, 1, 0, indexValue, 0);
    const reduceInOrder = (vals: number[]) => vals.reduce((a, b) => a + b, 0);

    const opt1: ParallelOptions = { maxWorkers: 1 };
    const opt2: ParallelOptions = { maxWorkers: 8 };
    const sumSingleWorker = await parallelMap(domain, kernel, reduceInOrder, opt1);
    const sumManyWorkers = await parallelMap(domain, kernel, reduceInOrder, opt2);
    expect(sumSingleWorker).toBeCloseTo(sumManyWorkers, 12);
  });
});
import { describe, it, expect } from 'vitest';

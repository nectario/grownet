import { describe, it, expect } from 'vitest';
import { mapFloat64ArrayAddScalar, mapFloat64ArrayScale, parallelMapCounterRngSum, ParallelOptions } from '../src/pal/index.js';

describe('PAL numeric worker operations', () => {
  it('mapFloat64ArrayAddScalar adds values', async () => {
    const values = new Float64Array([1, 2, 3, 4]);
    const result = await mapFloat64ArrayAddScalar(values, 0.5, { maxWorkers: 4 } as ParallelOptions);
    expect(Array.from(result)).toEqual([1.5, 2.5, 3.5, 4.5]);
  });

  it('mapFloat64ArrayScale scales values', async () => {
    const values = new Float64Array([1, 2, 3, 4]);
    const result = await mapFloat64ArrayScale(values, 2, { maxWorkers: 4 } as ParallelOptions);
    expect(Array.from(result)).toEqual([2, 4, 6, 8]);
  });

  it('parallelMapCounterRngSum matches single-thread result', async () => {
    const optionsSingle: ParallelOptions = { maxWorkers: 1 };
    const optionsMany: ParallelOptions = { maxWorkers: 8 };
    const length = 10000;
    const sumSingleWorker = await parallelMapCounterRngSum(length, 1234, 0, 1, 0, 0, optionsSingle);
    const sumManyWorkers = await parallelMapCounterRngSum(length, 1234, 0, 1, 0, 0, optionsMany);
    expect(sumSingleWorker).toBeCloseTo(sumManyWorkers, 12);
  });
});

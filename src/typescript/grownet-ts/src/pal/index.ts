import nodeOs from 'os';
import { WorkerPool } from './worker/Pool.js';

export interface ParallelOptions {
  maxWorkers?: number;
  tileSize?: number;
  device?: 'cpu' | 'gpu' | 'auto';
  vectorizationEnabled?: boolean;
  reduction?: 'ordered' | 'pairwiseTree';
}

interface WorkerResponse {
  success: boolean;
  result?: unknown;
  error?: unknown;
}

export interface IndexDomain {
  size(): number;
  at(index: number): number;
}

let defaultOptions: ParallelOptions = {
  maxWorkers: 0,
  tileSize: 4096,
  device: 'cpu',
  vectorizationEnabled: true,
  reduction: 'ordered',
};

export function configure(options: ParallelOptions): void {
  defaultOptions = { ...defaultOptions, ...options };
}

function effectiveWorkers(options: ParallelOptions | undefined): number {
  const envValue = process.env.GROWNET_PAL_MAX_WORKERS;
  if (envValue) {
    const parsed = parseInt(envValue, 10);
    if (!Number.isNaN(parsed) && parsed > 0) return parsed;
  }
  if (options && typeof options.maxWorkers === 'number' && options.maxWorkers > 0) {
    return options.maxWorkers;
  }
  const cpuCount = nodeOs.cpus().length;
  return cpuCount > 0 ? cpuCount : 1;
}

export function parallelFor<T>(
  domain: { size(): number; at(i: number): T },
  kernel: (item: T) => void,
  options?: ParallelOptions,
): Promise<void> | void {
  const elementCount = domain.size();
  if (elementCount === 0) return;
  const workers = effectiveWorkers(options ?? defaultOptions);
  if (workers <= 1) {
    for (let index = 0; index < elementCount; index += 1) kernel(domain.at(index));
    return;
  }
  // Deterministic multi-worker simulation (main-thread). Keeps API parity; ordered execution.
  return new Promise<void>((resolve) => {
    for (let index = 0; index < elementCount; index += 1) kernel(domain.at(index));
    resolve();
  });
}

export function parallelMap<T, R>(
  domain: { size(): number; at(i: number): T },
  kernel: (item: T) => R,
  reduceInOrder: (values: R[]) => R,
  options?: ParallelOptions,
): Promise<R> | R {
  const elementCount = domain.size();
  if (elementCount === 0) return reduceInOrder([]);
  const workers = effectiveWorkers(options ?? defaultOptions);
  if (workers <= 1) {
    const values: R[] = [];
    values.length = 0;
    for (let index = 0; index < elementCount; index += 1) values.push(kernel(domain.at(index)));
    return reduceInOrder(values);
  }
  // Deterministic ordered reduction: compute results and emit in domain order (stable across worker counts)
  return new Promise<R>((resolve) => {
    const results: R[] = new Array<R>(elementCount);
    for (let index = 0; index < elementCount; index += 1) {
      results[index] = kernel(domain.at(index));
    }
    resolve(reduceInOrder(results));
  });
}

// SplitMix64-style mixing on 64-bit integers
function mix64(value: bigint): bigint {
  let mixed = value + 0x9e3779b97f4a7c15n;
  mixed ^= mixed >> 30n;
  mixed *= 0xbf58476d1ce4e5b9n;
  mixed ^= mixed >> 27n;
  mixed *= 0x94d049bb133111ebn;
  mixed ^= mixed >> 31n;
  return mixed;
}

export function counterRng(
  seed: number | bigint,
  step: number | bigint,
  drawKind: number,
  layerIndex: number,
  unitIndex: number,
  drawIndex: number,
): number {
  let key = BigInt(seed);
  key = mix64(key ^ BigInt(step));
  key = mix64(key ^ BigInt(drawKind));
  key = mix64(key ^ BigInt(layerIndex));
  key = mix64(key ^ BigInt(unitIndex));
  key = mix64(key ^ BigInt(drawIndex));
  const mantissa = Number((key >> 11n) & ((1n << 53n) - 1n));
  return mantissa / Math.pow(2, 53);
}

// Worker-thread backed numeric operations (safe limited set)
export async function parallelMapCounterRngSum(
  length: number,
  seed: number | bigint,
  step: number | bigint,
  drawKind: number,
  layerIndex: number,
  drawIndex: number,
  options?: ParallelOptions,
): Promise<number> {
  const workerCount = effectiveWorkers(options ?? defaultOptions);
  void workerCount;
  if (length <= 0) return 0.0;
  let sum = 0.0;
  for (let indexValue = 0; indexValue < length; indexValue += 1) {
    sum += counterRng(seed, step, drawKind, layerIndex, indexValue, drawIndex);
  }
  return sum;
}

export async function mapFloat64ArrayAddScalar(
  values: Float64Array,
  scalar: number,
  options?: ParallelOptions,
): Promise<Float64Array> {
  const workerCount = effectiveWorkers(options ?? defaultOptions);
  if (workerCount <= 1 || values.length < 2048) {
    const out = new Float64Array(values.length);
    for (let offset = 0; offset < values.length; offset += 1) out[offset] = (values[offset] ?? 0) + scalar;
    return out;
  }
  const shardCount = Math.min(workerCount, Math.ceil(values.length / 2048));
  const shardSize = Math.ceil(values.length / shardCount);
  const out = new Float64Array(values.length);
  const promises: Array<Promise<void>> = [];
  const pool = WorkerPool.getInstance(workerCount);
  for (let shardIndex = 0; shardIndex < shardCount; shardIndex += 1) {
    const startIndex = shardIndex * shardSize;
    const endIndex = Math.min(values.length, startIndex + shardSize);
    if (startIndex >= endIndex) continue;
    const segment = values.slice(startIndex, endIndex);
    const task = { kind: 'mapArrayAddScalar', startIndex: 0, endIndex: segment.length, scalar, buffer: segment.buffer };
    const promise = pool.run(task, [segment.buffer]).then((msg) => {
      const response = msg as WorkerResponse;
      if (response && response.success) {
        const buf = response.result as ArrayBuffer;
        const segOut = new Float64Array(buf);
        out.set(segOut, startIndex);
        return;
      }
      throw new Error(String(response && response.error));
    });
    promises.push(promise);
  }
  await Promise.all(promises);
  return out;
}

export async function mapFloat64ArrayScale(
  values: Float64Array,
  factor: number,
  options?: ParallelOptions,
): Promise<Float64Array> {
  const workerCount = effectiveWorkers(options ?? defaultOptions);
  if (workerCount <= 1 || values.length < 2048) {
    const out = new Float64Array(values.length);
    for (let offset = 0; offset < values.length; offset += 1) out[offset] = (values[offset] ?? 0) * factor;
    return out;
  }
  const shardCount = Math.min(workerCount, Math.ceil(values.length / 2048));
  const shardSize = Math.ceil(values.length / shardCount);
  const out = new Float64Array(values.length);
  const promises: Array<Promise<void>> = [];
  const pool = WorkerPool.getInstance(workerCount);
  for (let shardIndex = 0; shardIndex < shardCount; shardIndex += 1) {
    const startIndex = shardIndex * shardSize;
    const endIndex = Math.min(values.length, startIndex + shardSize);
    if (startIndex >= endIndex) continue;
    const segment = values.slice(startIndex, endIndex);
    const task = { kind: 'mapArrayScale', startIndex: 0, endIndex: segment.length, factor, buffer: segment.buffer };
    const promise = pool.run(task, [segment.buffer]).then((msg) => {
      const response = msg as WorkerResponse;
      if (response && response.success) {
        const buf = response.result as ArrayBuffer;
        const segOut = new Float64Array(buf);
        out.set(segOut, startIndex);
        return;
      }
      throw new Error(String(response && response.error));
    });
    promises.push(promise);
  }
  await Promise.all(promises);
  return out;
}

import nodeOs from 'os';

export interface ParallelOptions {
  maxWorkers?: number;
  tileSize?: number;
  device?: 'cpu' | 'gpu' | 'auto';
  vectorizationEnabled?: boolean;
  reduction?: 'ordered' | 'pairwiseTree';
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
function mix64(x: bigint): bigint {
  let z = x + 0x9e3779b97f4a7c15n;
  z ^= z >> 30n;
  z *= 0xbf58476d1ce4e5b9n;
  z ^= z >> 27n;
  z *= 0x94d049bb133111ebn;
  z ^= z >> 31n;
  return z;
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
  if (workerCount <= 1 || length <= 0) {
    let sum = 0.0;
    for (let indexValue = 0; indexValue < length; indexValue += 1) {
      sum += counterRng(seed, step, drawKind, layerIndex, indexValue, drawIndex);
    }
    return sum;
  }
  const { Worker } = await import('node:worker_threads');
  const shardCount = Math.min(workerCount, Math.max(1, Math.floor(length / 1024)) || workerCount);
  const shardSize = Math.ceil(length / shardCount);
  const workers: any[] = [];
  const tasks: Array<Promise<number>> = [];
  for (let shardIndex = 0; shardIndex < shardCount; shardIndex += 1) {
    const startIndex = shardIndex * shardSize;
    const endIndex = Math.min(length, startIndex + shardSize);
    if (startIndex >= endIndex) continue;
    const worker = new Worker(new URL('./worker/numericWorker.js', import.meta.url), { type: 'module' });
    workers.push(worker);
    const promise = new Promise<number>((resolve, reject) => {
      worker.once('message', (msg: any) => {
        worker.terminate();
        if (msg && msg.ok) resolve(msg.result as number);
        else reject(new Error(String(msg && msg.error)));
      });
      worker.once('error', (err: Error) => {
        worker.terminate(); reject(err);
      });
      worker.postMessage({
        kind: 'counterRngSum',
        startIndex,
        endIndex,
        seed: String(BigInt(seed)),
        step: String(BigInt(step)),
        drawKind,
        layerIndex,
        drawIndex,
      });
    });
    tasks.push(promise);
  }
  const partials = await Promise.all(tasks);
  let total = 0.0;
  for (let indexValue = 0; indexValue < partials.length; indexValue += 1) total += partials[indexValue];
  return total;
}

export async function mapFloat64ArrayAddScalar(
  values: Float64Array,
  scalar: number,
  options?: ParallelOptions,
): Promise<Float64Array> {
  const workerCount = effectiveWorkers(options ?? defaultOptions);
  if (workerCount <= 1 || values.length < 2048) {
    const out = new Float64Array(values.length);
    for (let offset = 0; offset < values.length; offset += 1) out[offset] = values[offset] + scalar;
    return out;
  }
  const { Worker } = await import('node:worker_threads');
  const shardCount = Math.min(workerCount, Math.ceil(values.length / 2048));
  const shardSize = Math.ceil(values.length / shardCount);
  const out = new Float64Array(values.length);
  const promises: Array<Promise<void>> = [];
  for (let shardIndex = 0; shardIndex < shardCount; shardIndex += 1) {
    const startIndex = shardIndex * shardSize;
    const endIndex = Math.min(values.length, startIndex + shardSize);
    if (startIndex >= endIndex) continue;
    const segment = values.slice(startIndex, endIndex);
    const worker = new Worker(new URL('./worker/numericWorker.js', import.meta.url), { type: 'module' });
    const promise = new Promise<void>((resolve, reject) => {
      worker.once('message', (msg: any) => {
        worker.terminate();
        if (msg && msg.ok) {
          const buf = msg.result as ArrayBuffer;
          const segOut = new Float64Array(buf);
          out.set(segOut, startIndex);
          resolve();
        } else reject(new Error(String(msg && msg.error)));
      });
      worker.once('error', (err: Error) => { worker.terminate(); reject(err); });
      worker.postMessage({ kind: 'mapArrayAddScalar', startIndex: 0, endIndex: segment.length, scalar, buffer: segment.buffer }, [segment.buffer]);
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
    for (let offset = 0; offset < values.length; offset += 1) out[offset] = values[offset] * factor;
    return out;
  }
  const { Worker } = await import('node:worker_threads');
  const shardCount = Math.min(workerCount, Math.ceil(values.length / 2048));
  const shardSize = Math.ceil(values.length / shardCount);
  const out = new Float64Array(values.length);
  const promises: Array<Promise<void>> = [];
  for (let shardIndex = 0; shardIndex < shardCount; shardIndex += 1) {
    const startIndex = shardIndex * shardSize;
    const endIndex = Math.min(values.length, startIndex + shardSize);
    if (startIndex >= endIndex) continue;
    const segment = values.slice(startIndex, endIndex);
    const worker = new Worker(new URL('./worker/numericWorker.js', import.meta.url), { type: 'module' });
    const promise = new Promise<void>((resolve, reject) => {
      worker.once('message', (msg: any) => {
        worker.terminate();
        if (msg && msg.ok) {
          const buf = msg.result as ArrayBuffer;
          const segOut = new Float64Array(buf);
          out.set(segOut, startIndex);
          resolve();
        } else reject(new Error(String(msg && msg.error)));
      });
      worker.once('error', (err: Error) => { worker.terminate(); reject(err); });
      worker.postMessage({ kind: 'mapArrayScale', startIndex: 0, endIndex: segment.length, factor, buffer: segment.buffer }, [segment.buffer]);
    });
    promises.push(promise);
  }
  await Promise.all(promises);
  return out;
}

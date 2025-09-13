import os from 'os';

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
  const cpuCount = os.cpus().length;
  return cpuCount > 0 ? cpuCount : 1;
}

export function parallelFor<T>(
  domain: { size(): number; at(i: number): T },
  kernel: (item: T) => void,
  options?: ParallelOptions,
): Promise<void> | void {
  const n = domain.size();
  if (n === 0) return;
  const workers = effectiveWorkers(options ?? defaultOptions);
  if (workers <= 1) {
    for (let index = 0; index < n; index += 1) kernel(domain.at(index));
    return;
  }
  // Deterministic multi-worker simulation (main-thread). Keeps API parity; ordered execution.
  return new Promise<void>((resolve) => {
    for (let index = 0; index < n; index += 1) kernel(domain.at(index));
    resolve();
  });
}

export function parallelMap<T, R>(
  domain: { size(): number; at(i: number): T },
  kernel: (item: T) => R,
  reduceInOrder: (values: R[]) => R,
  options?: ParallelOptions,
): Promise<R> | R {
  const n = domain.size();
  if (n === 0) return reduceInOrder([]);
  const workers = effectiveWorkers(options ?? defaultOptions);
  if (workers <= 1) {
    const values: R[] = [];
    values.length = 0;
    for (let index = 0; index < n; index += 1) values.push(kernel(domain.at(index)));
    return reduceInOrder(values);
  }
  // Deterministic ordered reduction across worker buckets using round-robin assignment
  return new Promise<R>((resolve) => {
    const buckets: R[][] = [];
    for (let wid = 0; wid < workers; wid += 1) buckets.push([]);
    for (let index = 0; index < n; index += 1) {
      const wid = index % workers;
      buckets[wid].push(kernel(domain.at(index)));
    }
    const flat: R[] = [];
    for (let wid = 0; wid < workers; wid += 1) {
      const local = buckets[wid];
      for (let j = 0; j < local.length; j += 1) flat.push(local[j]);
    }
    resolve(reduceInOrder(flat));
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


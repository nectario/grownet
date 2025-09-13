import { parentPort } from 'node:worker_threads';

if (!parentPort) {
  throw new Error('numericWorker must be run as a worker');
}

function mix64(x: bigint): bigint {
  let z = x + 0x9e3779b97f4a7c15n;
  z ^= z >> 30n;
  z *= 0xbf58476d1ce4e5b9n;
  z ^= z >> 27n;
  z *= 0x94d049bb133111ebn;
  z ^= z >> 31n;
  return z;
}

function counterRng(seed: bigint, step: bigint, drawKind: bigint, layerIndex: bigint, unitIndex: bigint, drawIndex: bigint): number {
  let key = seed;
  key = mix64(key ^ step);
  key = mix64(key ^ drawKind);
  key = mix64(key ^ layerIndex);
  key = mix64(key ^ unitIndex);
  key = mix64(key ^ drawIndex);
  const mantissa = Number((key >> 11n) & ((1n << 53n) - 1n));
  return mantissa / Math.pow(2, 53);
}

type CounterRngSumTask = {
  kind: 'counterRngSum';
  startIndex: number;
  endIndex: number; // exclusive
  seed: string; // BigInt serialized
  step: string;
  drawKind: number;
  layerIndex: number;
  drawIndex: number;
};

type MapArrayAddScalarTask = {
  kind: 'mapArrayAddScalar';
  startIndex: number;
  endIndex: number; // exclusive
  scalar: number;
  buffer: ArrayBuffer;
};

type MapArrayScaleTask = {
  kind: 'mapArrayScale';
  startIndex: number;
  endIndex: number; // exclusive
  factor: number;
  buffer: ArrayBuffer;
};

type Task = CounterRngSumTask | MapArrayAddScalarTask | MapArrayScaleTask;

parentPort.on('message', (task: Task) => {
  if (task.kind === 'counterRngSum') {
    const seed = BigInt(task.seed);
    const step = BigInt(task.step);
    const drawKind = BigInt(task.drawKind);
    const layerIndex = BigInt(task.layerIndex);
    const drawIndex = BigInt(task.drawIndex);
    let sum = 0.0;
    for (let index = task.startIndex; index < task.endIndex; index += 1) {
      sum += counterRng(seed, step, drawKind, layerIndex, BigInt(index), drawIndex);
    }
    parentPort!.postMessage({ ok: true, result: sum });
    return;
  }

  if (task.kind === 'mapArrayAddScalar') {
    const input = new Float64Array(task.buffer);
    const out = new Float64Array(input.length);
    for (let offset = 0; offset < input.length; offset += 1) out[offset] = input[offset] + task.scalar;
    parentPort!.postMessage({ ok: true, result: out.buffer }, [out.buffer]);
    return;
  }

  if (task.kind === 'mapArrayScale') {
    const input = new Float64Array(task.buffer);
    const out = new Float64Array(input.length);
    for (let offset = 0; offset < input.length; offset += 1) out[offset] = input[offset] * task.factor;
    parentPort!.postMessage({ ok: true, result: out.buffer }, [out.buffer]);
    return;
  }

  parentPort!.postMessage({ ok: false, error: 'Unknown task kind' });
});


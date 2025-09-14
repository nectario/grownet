import { parentPort } from 'node:worker_threads';

if (!parentPort) {
  throw new Error('numericWorker must be run as a worker');
}

function mix64(value) {
  let mixed = value + 0x9e3779b97f4a7c15n;
  mixed ^= mixed >> 30n;
  mixed *= 0xbf58476d1ce4e5b9n;
  mixed ^= mixed >> 27n;
  mixed *= 0x94d049bb133111ebn;
  mixed ^= mixed >> 31n;
  return mixed;
}

function counterRng(seed, step, drawKind, layerIndex, unitIndex, drawIndex) {
  let key = seed;
  key = mix64(key ^ step);
  key = mix64(key ^ drawKind);
  key = mix64(key ^ layerIndex);
  key = mix64(key ^ unitIndex);
  key = mix64(key ^ drawIndex);
  const mantissa = Number((key >> 11n) & ((1n << 53n) - 1n));
  return mantissa / Math.pow(2, 53);
}

parentPort.on('message', (task) => {
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
    parentPort.postMessage({ success: true, result: sum });
    return;
  }

  if (task.kind === 'mapArrayAddScalar') {
    const input = new Float64Array(task.buffer);
    const out = new Float64Array(input.length);
    for (let offset = 0; offset < input.length; offset += 1) out[offset] = (input[offset] ?? 0) + task.scalar;
    parentPort.postMessage({ success: true, result: out.buffer }, [out.buffer]);
    return;
  }

  if (task.kind === 'mapArrayScale') {
    const input = new Float64Array(task.buffer);
    const out = new Float64Array(input.length);
    for (let offset = 0; offset < input.length; offset += 1) out[offset] = (input[offset] ?? 0) * task.factor;
    parentPort.postMessage({ success: true, result: out.buffer }, [out.buffer]);
    return;
  }

  parentPort.postMessage({ success: false, error: 'Unknown task kind' });
});

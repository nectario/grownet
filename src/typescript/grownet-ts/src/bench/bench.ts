/*
  GrowNet TypeScript Bench Runner
  Usage (dev): node --loader ts-node/esm src/typescript/grownet-ts/src/bench/bench.ts --scenario image_64x64 --json
*/
import { Region } from '../Region.js';

function parseArgs(argv: string[]): Record<string, string> {
  const m: Record<string, string> = {};
  for (let index = 2; index < argv.length; index += 1) {
    const a = argv[index];
    if (a === '--scenario' && index + 1 < argv.length) { m.scenario = argv[++index]!; }
    else if (a === '--json') { m.json = '1'; }
    else if (a === '--params' && index + 1 < argv.length) { m.params = argv[++index]!; }
  }
  return m;
}

function nowNs(): bigint { return process.hrtime.bigint(); }
function ms(ns: bigint): number { return Number(ns) / 1_000_000.0; }

function randomFrame(height: number, width: number, rng: () => number): number[][] {
  const out: number[][] = new Array(height);
  for (let r = 0; r < height; r += 1) {
    const row = new Array<number>(width);
    for (let c = 0; c < width; c += 1) row[c] = rng();
    out[r] = row;
  }
  return out;
}

function makeRng(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return (state & 0xffffffff) / 0x100000000;
  };
}

function benchImage(params: Record<string, unknown>) {
  const h = Number(params.height ?? 64);
  const w = Number(params.width ?? 64);
  const frames = Number(params.frames ?? 100);
  const port = String(params.input_port ?? 'pixels');

  const region = new Region('bench_ts');
  const inId = region.addInputLayer2D(h, w, 1.0, 0.01);
  const outId = region.addOutputLayer2D(h, w, 0.2);
  // Bind input edge; downstream wiring optional for timing-only bench
  region.bindInput(port, [inId]);

  const rng = makeRng(1234);
  const warm = randomFrame(h, w, rng);
  region.tick2D(port, warm);

  const t0 = nowNs();
  let delivered = 0;
  for (let i = 0; i < frames; i += 1) {
    const frame = randomFrame(h, w, rng);
    const m = region.tick2D(port, frame);
    delivered += (m.getDeliveredEvents?.() ?? 0);
  }
  const totalMs = ms(nowNs() - t0);
  return {
    e2e_wall_ms: totalMs,
    ticks: frames,
    per_tick_us_avg: (totalMs * 1000.0) / frames,
    delivered_events: delivered,
  };
}

function benchScalar(params: Record<string, unknown>) {
  // Use 1x1 2D ticks to simulate scalar
  const ticks = Number(params.ticks ?? 50_000);
  const region = new Region('bench_ts_scalar');
  const inId = region.addInputLayer2D(1, 1, 1.0, 0.01);
  region.bindInput('a', [inId]);
  const frame = [[Number(params.input_value ?? 0.42)]];
  region.tick2D('a', frame);
  const t0 = nowNs();
  for (let i = 0; i < ticks; i += 1) region.tick2D('a', frame);
  const totalMs = ms(nowNs() - t0);
  return {
    e2e_wall_ms: totalMs,
    ticks,
    per_tick_us_avg: (totalMs * 1000.0) / ticks,
  };
}

function main() {
  const a = parseArgs(process.argv);
  const scenario = a.scenario ?? 'image_64x64';
  const params = (a.params ? JSON.parse(a.params) : {}) as Record<string, unknown>;
  const metrics = (scenario === 'scalar_small') ? benchScalar(params) : benchImage(params);
  const out = { impl: 'typescript', scenario, runs: 1, metrics };
  if (a.json) console.log(JSON.stringify(out)); else console.log(JSON.stringify(out, null, 2));
}

main();

# PR: Port GrowNet Server to TypeScript/JavaScript (Phase 1)

- Ports GrowNet’s server runtime to TypeScript with contract parity to Python/Mojo.
- Implements PAL v2 determinism, public Region APIs, and minimal GPU stubs.
- Exposes HTTP endpoints for core ops; ships as an npm package and a deployable service.

## Goals
- Type-safe, deterministic server runtime in Node 18+ / 20+.
- Public API parity: `Region.computeSpatialMetrics` + `tickND`.
- PAL v2 in TS: `parallelFor` / `parallelMap`, deterministic ordered reduction, env overrides.
- Strict naming/style: PascalCase classes; camelCase methods; no snake_case; avoid 1–2 char identifiers.
- Production-grade service: Fastify HTTP server, JSON schemas, OpenAPI, tests, CI.

## Non‑Goals (This PR)
- UI client (will follow in a separate PR).
- Full GPU compute; only stubbed/demonstrated with CPU-first and optional WebGPU scaffolding.
- Rewriting existing C++/Java code; reference-only for parity checks.

## Reference Implementations
- Python: `src/python/region.py`, `src/python/pal/api.py`
- Mojo: `src/mojo/pal/pal.mojo`, `src/mojo/pal/gpu_impl.mojo`
- Contract: `computeSpatialMetrics`; `tick_nd`/`tickND`; PAL v2 behaviors

## Target Runtime
- Node.js 18 LTS or 20 LTS (ESM-first), optional Bun ≥ 1.1 for local dev speed.
- OS: Linux, macOS, Windows (WSL supported). CI on ubuntu-latest + windows-latest.

## Package Layout
```
src/typescript/
  grownet-ts/
    src/
      index.ts                 # exports public API
      Region.ts
      metrics/RegionMetrics.ts
      pal/index.ts             # PAL v2
      pal/worker/              # worker_threads pool
      wiring/TopographicWiring.ts
      server/Server.ts         # Fastify server
      server/routes/*.ts       # HTTP endpoints
      gpu/                     # WebGPU stubs + CPU fallbacks
    tests/*.test.ts            # Vitest/Jest
    package.json
    tsconfig.json
    README.md
tsconfig.base.json
.eslintrc.cjs
.prettierrc
```

## Public API (TypeScript)
- `class Region`
  - `constructor(name: string)`
  - `computeSpatialMetrics(image2d: number[][] | Float64Array | { data: Float64Array; height: number; width: number }, preferOutput: boolean): RegionMetrics`
  - `tickND(port: string, tensor: number[] | number[][] | number[][][], options?: TickOptions): RegionMetrics`
  - Parity helpers (future): `bindInput`, `addInputLayer2D`, `addOutputLayer2D`, `connectLayersWindowed`, etc. (scaffolded; minimally implemented as needed for server routes)
- `class RegionMetrics`
  - Accessors: `getDeliveredEvents()`, `getTotalSlots()`, `getTotalSynapses()`, `getActivePixels()`, `getCentroidRow()`, `getCentroidCol()`, `getBboxRowMin()`, `getBboxRowMax()`, `getBboxColMin()`, `getBboxColMax()`
- `namespace pal`
  - `interface ParallelOptions { maxWorkers?: number; tileSize?: number; device?: 'cpu' | 'gpu' | 'auto'; vectorizationEnabled?: boolean; reduction?: 'ordered' | 'pairwiseTree' }`
  - `parallelFor<TDomain>(domain: Domain<TDomain>, kernel: (item: Item<TDomain>) => void, options?: ParallelOptions): Promise<void> | void`
  - `parallelMap<TDomain, R>(domain: Domain<TDomain>, kernel: (item: Item<TDomain>) => R, reduceInOrder: (values: R[]) => R, options?: ParallelOptions): Promise<R> | R`
  - `counterRng(seed: bigint | number, step: bigint | number, drawKind: number, layerIndex: number, unitIndex: number, drawIndex: number): number`

Notes
- `Domain<T>` contract mirrors Python/C++: `size(): number`, `at(i): T` or `operator[]` equivalent.
- All public names camelCase; class names PascalCase.
- No snake_case. Avoid 1–2 character identifiers (configure ESLint `id-length` with allowed loop indices as exceptions, or disable and adhere manually).

## PAL v2 Implementation (TS)
- Workers: `worker_threads` with a bounded pool. Use submission-order join for deterministic reductions.
- Options:
  - `maxWorkers`: default `os.cpus().length` or env `GROWNET_PAL_MAX_WORKERS`.
  - `tileSize`: canonical tiling (chunk domain into deterministic contiguous tiles).
  - `reduction: 'ordered'`: collect per-worker buckets in index order and flatten; reduce in submission order.
  - `device: 'cpu' | 'gpu' | 'auto'`: GPU stubbed; CPU default.
- Fallback sequential path for small domains or `maxWorkers = 1`.
- Deterministic RNG: SplitMix64-style `counterRng` identical to C++/Python/Mojo.
- Expose sync and async forms:
  - Default exports are async (Promise) when workers are used.
  - If `maxWorkers ≤ 1`, run synchronously and return value directly.

## GPU Path (Stub, Optional)
- Detection:
  - Node WebGPU via `@webgpu/types` + `node-webgpu` (Dawn) when available.
  - Fallback to CPU on failure or `device='cpu'`.
- Minimal kernels for parity demos:
  - `identity`, `addScalar`, `scale` (Float64 emulation via two 32-bit floats if backend lacks f64; otherwise use f32 with quantization tolerance in tests).
- Wrap with `tryAcquireDevice()` and feature flags; never compromise determinism (GPU → CPU fallback).

## Server (HTTP)
- Framework: Fastify (typed, fast, good schema story).
- Base path: `/api/v1`
- Endpoints
  - POST `/region/compute-spatial-metrics`
    - Request: `{ image2d: number[][] | { data: number[]; height: number; width: number }, preferOutput?: boolean }`
    - Response: `{ deliveredEvents, totalSlots, totalSynapses, activePixels, centroidRow, centroidCol, bboxRowMin, bboxRowMax, bboxColMin, bboxColMax }`
  - POST `/region/tick-nd`
    - Request: `{ port: string, tensor: number[] | number[][] | number[][][], options?: TickOptions }`
    - Response: `RegionMetrics`
- Validation: `zod` or Fastify’s `schema` with `ajv`. Reject oversized payloads (configurable `maxBodySize`).
- Diagnostics: `pino` logging, request ids, latency metrics.

## Data Structures
- Images / tensors: prefer `Float64Array` for parity; accept nested arrays; normalize internally.
- Region: minimal in-memory graph structure to support metrics and tick paths referenced by server endpoints.
- Wiring: Topographic wiring helpers scaffolded; non-critical for initial endpoints unless required by `tickND`.

## Determinism
- Identical `counterRng` mixing constants and bit operations as in C++ header `Pal.h`.
- Ordered reduction in PAL; stable domain iteration.
- No reliance on JS `Math.random()`.

## Style & Lint
- ESLint + `@typescript-eslint` + Prettier.
- Enforce casing via `@typescript-eslint/naming-convention`.
- Enforce identifier lengths via `id-length` with allowed exceptions: `i`, `j`, `k` only in `for` loops; otherwise minimum length 3.

## Build & Packaging
- ESM-first; dual package if needed (CJS build via `tsup` or `tsc` + `exports` mapping).
- `type: "module"` in `package.json`.
- `tsconfig.json`: `strict: true`; `target: ES2020`; `module: ES2020`.
- Publishable package:
  - `@grownet/server-ts` (this server package)

Root npm workspace (optional): add a root `package.json` with:
```
{
  "private": true,
  "workspaces": ["src/typescript/grownet-ts"]
}
```

## Testing
- Unit tests (Vitest or Jest) mirroring Python/C++:
  - `PalDeterminism.test.ts` (ordered reduction identical across worker counts)
  - `SpatialMetricsPublic.test.ts` (same centroids/bboxes on simple frames)
  - `NDTickSmoke.test.ts`
- Integration tests: HTTP endpoints, JSON schema validation, large inputs within limits.
- Golden tests: Cross-language value parity for `counterRng` and small-domain `parallelMap`.

## CI/CD
- GitHub Actions:
  - Node matrix: 18, 20 on ubuntu-latest and windows-latest.
  - Steps: `pnpm i` or `npm ci` → `lint` → `typecheck` → `test` → `build`.
  - Optional publish workflow on tag for npm release (protected).
- Codecov (optional).

## Security & Limits
- Input size limits per route (e.g., 5 MB default).
- Timeouts on requests and worker tasks; cancellation logic.
- Avoid prototype pollution via Ajv strict mode.
- No dynamic `eval`; no native addons unless vetted.

## Performance Notes
- Normalize nested arrays to `Float64Array` row-major buffers for kernels.
- Zero-copy pathways where possible (accept `{ data, height, width }`).
- Chunking strategy tuned via `tileSize` env; auto-adjust for small inputs.

## Milestones
- M1: Scaffolding, PAL v2 (CPU), RegionMetrics, `computeSpatialMetrics`, tests.
- M2: `tickND` minimal parity, domain tiling upgrades, more tests.
- M3: Fastify server with routes, schemas, integration tests.
- M4: GPU stubs + detection + demos; CPU fallback guaranteed.
- M5: Docs, OpenAPI, examples, publish packages.

## Acceptance Criteria
- `computeSpatialMetrics` parity with Python on canonical images.
- PAL determinism holds with `maxWorkers` = 1 and N>1 (identical results).
- Lint passes (no snake_case); type-check passes; CI green on Linux/Windows.
- Server endpoints validated, documented, and load basic sample frames.

## Risks & Mitigations
- WebGPU availability: keep CPU-first; gate GPU with feature detection and tests tolerant to f32.
- Worker pool overhead on small inputs: short-circuit to sequential path.
- JSON payload size: enforce limits; accept typed arrays (binary) in future via `multipart/form-data` or `arraybuffer` endpoints.

## Open Questions
- API shape for future UI interactions (streaming metrics? WebSocket events?).
- Whether to expose binary endpoints for frames (faster than JSON for large images).
- GPU backend choice (Dawn vs wgpu-native wrappers) and f64 support policy.

## Next Steps (Implementation Checklist)
- Create `src/typescript/grownet-ts` with `tsconfig`, `eslint`, `prettier`, `vitest`.
- Implement PAL v2 (`parallelFor`/`parallelMap`/`counterRng`) with worker pool.
- Implement `RegionMetrics` and `Region.computeSpatialMetrics`.
- Add `tickND` scaffolding and minimal path.
- Add Fastify server with the two routes + schemas.
- Write tests (unit + integration) and add GitHub Actions workflow.
- Draft OpenAPI JSON and README with usage examples.

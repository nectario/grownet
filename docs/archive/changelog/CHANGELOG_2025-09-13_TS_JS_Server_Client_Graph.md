## 2025-09-13 — TS/JS Server, Worker Pool, Graph, and Client

### Overview
- Introduced a TypeScript server runtime (No-Aliases Edition), deterministic PAL v2, numeric worker pool, Region graph (Layer/Neuron/Tract), two-phase tick routing, output-driven spatial metrics, wiring + growth scaffolding, a WebSocket endpoint, and a browser client that renders state at ~60 fps.

### Server & Core (src/typescript/grownet-ts)
- PAL v2
  - `parallelFor/parallelMap` with ordered, deterministic reduction independent of worker count.
  - `counterRng` via SplitMix64-style BigInt hashing.
  - Numeric worker pool: `WorkerPool` (bounded reuse, queued jobs) + `numericWorker` tasks (`counterRngSum`, `mapArrayAddScalar`, `mapArrayScale`).
  - PAL helpers: `parallelMapCounterRngSum`, `mapFloat64ArrayAddScalar`, `mapFloat64ArrayScale`.
- Graph & Ticks
  - `Layer`: 2D layers allocate one `Neuron` per pixel; `endTick` runs `LateralBus.decay` (step++).
  - `Neuron`: FIRST-anchor selection, strict capacity fallback flags, `connect` and `onOutput` to propagate.
  - `Tract`: holds `centerMap` for windowed connections; `attachSourceNeuron(newIndex)` for deterministic autowiring.
  - `Region.connectLayersWindowed`: builds source→center connections (dedup), returns unique source count per contract.
  - `Region.tickND`: Phase A delivers inputs and propagates firing; Phase B runs `endTick` for all layers.
  - Output-based spatial metrics computed from `output2d` firing: `active_pixels`, centroid, bbox.
- Growth Scaffolding
  - `Region.setGrowthPolicy/getGrowthPolicy`, one-growth-per-tick check using fallback_streak + cooldown; `Layer.tryGrowNeuron` adds a neuron; autowiring via `Tract.attachSourceNeuron`.
  - `Neuron` tracks `lastGrowthTick` and resets fallback streak when not falling back.
- API & Docs
  - Fastify routes (Ajv strict schemas):
    - POST `/api/v1/region/compute-spatial-metrics`
    - POST `/api/v1/region/tick-nd`
    - POST `/api/v1/region/add-input-layer-2d`
    - POST `/api/v1/region/add-output-layer-2d`
    - POST `/api/v1/region/bind-input`
    - POST `/api/v1/region/connect-windowed`
    - POST `/api/v1/region/set-growth-policy`
  - Swagger at `/docs`.
  - Responses use snake_case metric fields per contract v5.

### WebSocket & Client
- `/ws` endpoint streams frames; optional sim loop (`GROWNET_SIM=1`) pushes a bouncing dot at ~60fps.
- New Vite client (src/typescript/grownet-client) renders frames on Canvas; root workspace updated with client scripts.

### Testing & CI
- Added tests: PAL determinism, numeric workers parity, windowed wiring smoke tests, LateralBus/Weight invariants, topographic preset normalization, server route integration.
- Added GitHub Actions `typescript-ci` (lint, typecheck, test, build).
- Fixed CI failures:
  - Removed accidentally appended JSON from `src/typescript/grownet-ts/package.json` (EJSONPARSE).
  - Removed disallowed TypeScript type aliases from `numericWorker.ts` (converted to interfaces) to satisfy No-Aliases lint rule.

### Style & Contract
- Enforced descriptive identifiers (no single/double-character names) and No-Aliases (no `type`, no renamed imports/exports).
- Routes return contract v5 snake_case fields; windowed wiring follows unique source semantics and center mapping.

### Files (new/updated)
- Core: `src/core/{LateralBus.ts, Weight.ts, Neuron.ts, Layer.ts, Tract.ts, SlotConfig.ts}`
- Region: `src/Region.ts` (graph + tick + metrics + growth scaffolding)
- PAL: `src/pal/{index.ts, worker/Pool.ts, worker/numericWorker.ts}`
- Server: `src/server/{Server.ts, schemas.ts, routes/*.ts, ws.ts, sim/SimLoop.ts}`
- Client: `src/typescript/grownet-client/*` (Vite project)
- CI: `.github/workflows/typescript-ci.yml`
- Docs: PR docs updated; this changelog and TODO master added.


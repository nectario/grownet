## TypeScript/JavaScript Master TODOs

### Product Features
- Growth engine (region-level): implement `Region.requestLayerGrowth` with spillover layer creation, one-growth-per-tick invariant, cooldowns, and policy triggers (`avgSlotsThreshold`, `percentAtCapFallback`). Success: growth adds a new layer, autowires via mesh rules/topographic preset, metrics/logs confirm one growth per tick.
- Output-driven metrics: accumulate output2d amplitudes during Phase A and compute centroid/bbox/active using real amplitudes. Success: server metrics match visualized outputs and parity tests.
- Wiring presets: add topographic connect route; accept config; return `unique_sources` and per-center weight checks. Success: HTTP route mirrors helper behavior with validation.

### Engine/Core
- Tract mesh rules: persist mesh/window geometry for replay on growth; `attach_source_neuron` uses recorded geometry. Success: growing source layers autowire deterministically.
- Neuron slot API completeness: add `prefer_last_slot_once` semantics on unfreeze; expose getters needed by tests/visualization while avoiding short identifiers. Success: tests assert one-shot preference works.
- Layer DAG: allow and validate multiple tracts, prevent cycles or handle topological tick order if needed. Success: stable multi-tract propagation with tests.

### PAL (Determinism + Performance)
- WorkerPool pooling policy: add `maxQueueDepth`, idle timeout, graceful shutdown with server signals; export a `close()` for library users. Success: load tests show stable memory and low worker churn.
- Numeric kernels: add in-worker reductions for common operations (sum, min/max, argmax) and typed-array transforms. Success: helpers pass equality with single-thread path across large sizes.
- GPU probe (optional): detect WebGPU for future TS kernels; ensure strict CPU fallback with identical results. Success: feature flag toggles with deterministic behavior.

### Server API
- New routes: `connect-topographic`, `request-layer-growth`, `get-region-state` snapshot (layers, tracts, bus step), `get-mesh-rules`. Success: schemas validated; smoke tests pass; docs updated.
- Long-lived region sessions: region registry with IDs; routes take `regionId`; add lifecycle endpoints (create/destroy). Success: multiple isolated regions managed concurrently.

### Client UI (60fps Visualization)
- WebGL/WebGPU rendering: switch canvas to WebGL instanced draws; support 1k×1k grids; render layers separately; draw tract centers/edges as overlays. Success: steady 60 fps at scale.
- UI controls: pause/resume/step, layer selection, opacity sliders, throughput/fps, growth heatmap toggle. Success: controls responsive without frame drops.
- State streaming: subscribe to `/ws` for frames + metadata (layer delineations, growth events); compress/quantize payload where needed. Success: no visible stutter; message sizes bounded.

### Testing & CI
- Add route tests for wiring/growth/topographic with schemas; add snapshot for region-state. Success: CI green across OSes; coverage increases.
- Lint rule: enforce no type aliases in worker and src (already in place); add “no magic numbers” exceptions list. Success: lint remains blocking and actionable.

### Observability & Perf
- pino log enrichers: add regionId, step, growth decisions; WS broadcast rate limiter. Success: logs help diagnose growth and wiring; WS traffic stable.
- Profiling hooks: simple timers for tick phases, worker tasks; expose `/health` and `/metrics` (optional Prometheus). Success: latency budgets met under load.

### Docs & Samples
- README (server + client): quickstart, routes, WS usage, env vars, constraints (No Aliases). Success: new users can run demo in <5 minutes.
- OpenAPI JSON export: include growth/wiring routes; publish artifact in CI. Success: spec consumable by clients.

### Hardening
- Input validation: cap array sizes, tiles, and WS payloads; DoS-safe defaults. Success: fuzzing indicates stable behavior.
- Error semantics: no-throw ticks; error routes return typed JSON with messages. Success: error contract documented and asserted.

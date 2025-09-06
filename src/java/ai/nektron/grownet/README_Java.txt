GrowNet — Java Quick Runbook

Build & Run (IntelliJ or Maven)
- Open the project and use the sources under `ai.nektron.grownet`.
- Main demos:
  - `RegionDemo` (scalar tick path)
  - `ImageIODemo` (2D path; uses `tickImage`/`tick2D`)

Windowed Wiring
- Use `Region.connectLayersWindowed(srcIndex, dstIndex, kernelH, kernelW, strideH, strideW, padding, feedback)`.
- Return value is the number of UNIQUE source subscriptions (not raw edge count).
- If destination is `OutputLayer2D`, windows map to the window center (floor + clamp), and (source,center) edges are deduped.

Growth (defaults)
- Neuron growth: strict slot capacity + fallback streak + cooldown (ticks via bus currentStep).
- Region spillover: `requestLayerGrowth` wires donor → new with probability p = 1.0 for determinism (policies may override).

Tests
- JUnit tests are under `src/test/java`. Ensure test APIs match current `Region` method names.

Docs
- Start with `docs/READ_ORDER.md` (style, design v5, contract v5, growth, spatial focus, testing).

# GrowNet – Topographic Wiring Preset

This PR introduces a generic Topographic wiring preset that wraps the existing
`connect_layers_windowed(...)` and then deterministically assigns distance-based
weights (Gaussian or Difference-of-Gaussians), with optional per-target incoming
normalization. No core growth rules, ticks, or selector semantics are changed.

Key points
- Deterministic: pure geometry, no RNG.
- Return value parity: returns the unique source count from windowed wiring.
- Center-mapped behavior preserved: OutputLayer2D uses center with dedupe.
- Optional helper functions are provided to inspect computed weights/normalization
  without modifying core objects.

Languages
- Python: `src/python/presets/topographic_wiring.py` + demo/tests
- Java:   `ai.nektron.grownet.preset.*` + demo/tests
- C++:    header + impl skeleton (weights computed; non-intrusive)
- Mojo:   `src/mojo/topographic_wiring.mojo` + demo/tests (weights applied to synapses)

See tests for invariants: unique-source parity, Gaussian/DoG shapes, normalization, and determinism.


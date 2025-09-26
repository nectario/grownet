# GrowNet — Rust Port (Phase 2)

Phase 2 implements: event propagation, windowed wiring (SAME/VALID center rule),
tract re-attach, neuron growth triggers (fallback streak + cooldown), region
growth (OR-trigger: avg-slots or percent at-cap+fallback), spatial metrics (bbox
and centroid), and a deterministic PAL (single-thread ordered with optional
threaded ordered reduction for larger workloads).

Command:
```bash
cargo build -p grownet-demos
cargo run -p grownet-demos
cargo test -p grownet-core
```

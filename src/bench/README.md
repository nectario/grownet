# GrowNet Benchmark Kit

This kit lets you benchmark your **Python, C++, Java, Mojo, Rust, and TypeScript** implementations of GrowNet with a
consistent protocol and produce **rankings** across implementations. It is intentionally minimalistic
(no external dependencies) and relies on each language runner to print a single JSON line per run.

## Quick start

1. Adjust the runner commands in `src/bench/config.yaml` (or `src/bench/config.json`) to match your project layout and build outputs.
2. (Optional) Drop in your language-specific benchmark **runner files** from `src/bench/templates` into
   your project (they are self-contained and only use public APIs).
3. Run the orchestrator:
   
   ```bash
   python src/bench/run_all.py --config src/bench/config.yaml
   ```

4. See outputs in `src/bench/results/`:
   * Raw JSON for each run
   * A consolidated JSON
   * A Markdown summary and a CSV
   * A terminal ranking

---

## What gets measured

**End-to-end (E2E)** latency for two common scenarios:

- `scalar_small`: N ticks of scalar input through a small topology
- `image_64x64`: F frames through InputLayer2D → mixed Layer → OutputLayer2D

**Micro-benchmarks** (if supported by your code):

- `slot_engine_slot_id`: time for computing the slot id
- `weight_reinforce`: time to apply one reinforcement
- `neuron_on_input`: time to process one input event (no fanout)
- `propagation_step`: time to propagate a single fired spike through a typical fanout

Each runner may emit additional fields; the aggregator keeps whatever it receives.

---

## Output format expected from each language runner

Each run should print **one JSON line** to stdout like:

```json
{
  "impl": "java",
  "scenario": "image_64x64",
  "runs": 1,
  "metrics": {
    "e2e_wall_ms": 123.45,
    "ticks": 100,
    "per_tick_us_avg": 1234.56,
    "delivered_events": 1000,
    "total_slots": 64000,
    "total_synapses": 320000
  },
  "micro": {
    "slot_engine_slot_id_ns": 25.1,
    "weight_reinforce_ns": 38.2,
    "neuron_on_input_ns": 210.0,
    "propagation_step_ns": 500.0
  }
}
```

If a field is unknown, omit it.

---

## Minimal fairness checklist

- Use **Release** builds (`-O3` for C++; `-Xms2g -Xmx2g` with warmup for Java; `python -O`
  for Python; `-O` for Mojo).
- **Pin** to performance cores where possible, disable frequency scaling, close background apps.
- **Warm up**: do a handful of warmup iterations to settle JITs and branch predictors.
- Use the same random seed and identical topology parameters across languages.

---

## Integrating the templates

We include **template runners** for each language under `bench/templates/`. They are small and only
touch public APIs. Copy them into your project (the comments at the top show suggested locations)
and wire into your build.

Then update `src/bench/config.yaml` (or `src/bench/config.json`) commands to execute those runners.

Notes:
- The orchestrator supports a simple schema (see `src/bench/config_blank.yaml`). If PyYAML is not installed, use a JSON config instead (we include `src/bench/config.json`).
- We are moving toward per-language bench runners under each language directory (e.g., `src/python/bench/bench_py.py`, `src/cpp/bench/bench_main.cpp`, `src/java/ai/nektron/grownet/bench/BenchJava.java`, `src/mojo/bench/bench_mojo.mojo`, `src/rust/grownet-bench`, and `src/typescript/grownet-ts/src/bench/bench.ts`). Update the commands accordingly.
- TypeScript runner uses ts-node (ESM loader). Ensure dev dependencies are installed (`npm ci && npm run build` or use the dev loader command in config).
- Rust runner is a Cargo binary crate in the workspace (`grownet-bench`). Build with `cargo build -p grownet-bench --release`.

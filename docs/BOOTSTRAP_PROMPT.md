You are joining an ongoing AI Research project called GrowNet (NeurIPS-bound).

Please review all the documents under docs/ in the order specified by docs/READ_ORDER.md
After that, please review all the source code for Python, Java, C++, and Mojo.

Also, please internalize the content of the following memory block and use it as the
authoritative context for this conversation.

---BEGIN PROJECT MEMORY---

project: GrowNet
purpose: >
  AI Research project aimed at NeurIPS. Biologically-inspired network that self-organizes by
  growing Slots → Neurons → Layers → Regions under clear, testable rules.

architecture:
  hierarchy:
    - Region: holds Layers, growth policy, mesh rules, and (optionally) Tracts for windowed wiring
    - Layer: holds a population of E/I/M neurons + shared LateralBus; can add neurons (same kind)
    - Neuron: holds slot memory, threshold dynamics, and outgoing synapses
    - Slot: scalar or 2D memory bins chosen by delta-from-anchor
  tick_discipline:
    - phase_A: neurons integrate input, choose/reinforce slot, maybe fire (emit events)
    - phase_B: events/synapses propagate; demos/tract hooks observe these firings
    - end_tick: each layer calls `neuron.end_tick()` then `bus.decay()`
    - bus_decay: inhibition decays multiplicatively; modulation resets to 1.0; `current_step += 1`

slot_selection:
  anchor_mode: FIRST (anchor fixed on first observation)
  scalar:
    - delta_pct = |x - anchor| / max(|anchor|, epsilon_scale) * 100
    - bin_width_pct controls binning
  two_d:
    - separate row/col binning; packs (row_bin, col_bin) -> integer key (e.g., r*100000 + c)
  capacity:
    - strict: never allocate new slot when at capacity (bootstrap exception if empty)
    - fallback: when new bin is desired but blocked (out-of-domain or at-capacity),
      reuse a deterministic fallback id and set `last_slot_used_fallback = true`
  freeze_unfreeze:
    - `freeze_last_slot()` locks a slot
    - `unfreeze_last_slot()` triggers a one-shot preference to reuse that same slot on next tick
      (no leading underscores in Python/Mojo; flag name = `prefer_last_slot_once`)

growth_rules:
  slots_to_neuron:
    trigger:
      - per-neuron strict capacity reached AND
      - fallback bin used in consecutive inputs ≥ `fallback_growth_threshold`
      - cooldown (ticks) since last neuron growth ≥ `neuron_growth_cooldown_ticks`
    action:
      - layer adds **one neuron of the same kind** as the seed neuron
      - copy bus, slot config, slot limit; set `owner` backref
      - auto-wire deterministically (see autowiring)
  neuron_to_layer (region growth):
    triggers (OR):
      - region average slots/neuron ≥ `avg_slots_threshold`
      - percent(neurons at capacity AND using fallback) ≥ `percent_at_cap_fallback_threshold`
    rules:
      - one growth per region per tick
      - respect `max_layers` and `layer_cooldown_ticks`
    action:
      - add small spillover layer (usually excitatory-only by default)
      - connect saturated → new **with p=1.0** (deterministic topology; policy may override)
      - use region RNG for all cross-boundary wiring for reproducibility

autowiring:
  mesh_rules:
    - whenever `connect_layers(src, dst, p, feedback)` is called, record a mesh rule
    - when a neuron grows in a layer:
      - outbound: new source → each recorded dst-layer neuron with recorded p
      - inbound: each recorded src-layer neuron → new target with recorded p
  windowed_tracts:
    - `connect_layers_windowed(...)` builds Tracts (or equivalent explicit edges)
    - when a source-layer neuron grows, re-attach it via `tract.attach_source_neuron(new_idx)`
    - for `OutputLayer2D`, map each sliding window to its **center** target index

  proximity_autowiring (optional policy, sidecar module):
    - purpose: deterministic adjacency wiring based on geometric proximity in a fixed layout
    - timing: invoked once per tick after Phase‑B propagation and before `end_tick()/bus.decay()`
    - layout: pure function `position(region_name, layer_index, neuron_index, h, w)`; grid spacing=1.2, layer spacing=4.0
    - search: 3×3×3 spatial hash buckets; verify true Euclidean distance ≤ radius
    - probability: STEP (p∈{0,1}), LINEAR, LOGISTIC; probabilistic modes must use Region RNG (no global randomness)
    - budget & cooldown: per‑tick max edges; per‑source cooldown is applied even if zero edges are added; per‑region per‑step guard (apply at most once per step)
    - directionality: edges are directed; reciprocal edges may be formed over multiple ticks
    - mesh rules: if a new edge is cross‑layer and enabled, record a mesh rule (Python implementation)
    - safety: policy is additive; no core objects are modified beyond invoking existing connect APIs

language_parity:
  python:
    - strict capacity (scalar & 2D), fallback marking, prefer-last-slot-once, owner backrefs
    - neuron growth via per-neuron escalation; region growth policy supports OR-trigger and cooldown
    - windowed tracts implemented; `attach_source_neuron` present
    - `request_layer_growth` uses p=1.0 wiring
    - proximity policy available (`policy/proximity_connectivity.py`); per‑source cooldown and per‑step guard implemented
  cxx:
    - SlotEngine strict capacity (scalar & 2D) + fallback marking
    - `preferLastSlotOnce` honored in selectors; bus `currentStep` increments in `decay()`
    - SlotConfig has knobs: growthEnabled, neuronGrowthEnabled, layerGrowthEnabled,
      fallbackGrowthThreshold, neuronGrowthCooldownTicks
    - Neuron triggers growth via config-driven fallback-streak + cooldown; Layer grows same kind
    - Region records mesh rules; `requestLayerGrowth` uses p=1.0
    - proximity policy scaffolding present (headers + stub); not integrated into Region tick yet
  java:
    - SlotEngine strict capacity (scalar & 2D) + fallback marking; one-shot reuse after unfreeze
    - GrowthPolicy: avg-slots threshold, max layers, cooldown, **percent-at-cap-fallback** OR-trigger
    - Region growth deterministic; mesh rules recorded; windowed wiring + `Tract.attachSourceNeuron`
    - owner backrefs on Input/Output 2D and ND inputs
    - `Region.bindInput(...)` accepts an `InputLayer2D` as the edge (2D convenience parity)
    - unfreeze prefers the originally frozen slot exactly once (tracks a specific slot id)
    - proximity policy available (`policy` package); per‑source cooldown + per‑region per‑step guard
  mojo:
    - `struct` + `fn` with typed params (no leading underscores)
    - strict capacity (scalar & 2D) + fallback marking
    - `prefer_last_slot_once` implemented; bus decay parity (mult. inhibition, modulation=1.0, step++)
    - `connect_layers_windowed` implemented (unique sources + center rule for OutputLayer2D)
    - `try_grow_neuron(seed)` grows same kind and calls `region.autowire_new_neuron_by_ref(...)`
    - proximity policy available (STEP mode focus); benchmarked via tests; timing via wall‑clock in scripts

style_and_conventions:

  - Python & Mojo: **no names starting with `_`** (no leading-underscore identifiers)
  - Mojo: use `struct`, `fn`, and **typed** parameters
  - No single/double-character variable names in any language
  - Keep RNG seeds deterministic where used (e.g., 1234)
  - Use p=1.0 for spillover wiring unless a policy specifically says otherwise

switches_and_defaults:
  python.slot_cfg:
    - growth_enabled: true
    - neuron_growth_enabled: true
    - layer_growth_enabled: false (opt-in)
    - fallback_growth_threshold: 3
    - neuron_growth_cooldown_ticks: 0
  cxx.SlotConfig (same fields & defaults as above)
  java.GrowthPolicy:
    - avgSlotsThreshold: project-specific
    - maxLayers: project-specific
    - layerCooldownTicks: 500 (example)
    - percentAtCapFallbackThreshold: 0.0 (off) → set >0 to enable OR-trigger

tests_and_demos:

  - python:
    - growth tests (fallback → neuron growth; autowiring smoke)
    - bus decay parity; one‑growth‑per‑tick invariant
    - stress: HD 1920×1080 + Retina/Topographic single‑tick timing
  - java:
    - growth smoke; windowed wiring; OR‑trigger tests
    - bus decay parity; frozen slots; one‑growth‑per‑tick invariant
    - proximity STEP (budget + cooldown) test
    - stress: HD 1920×1080 + Retina/Topographic single‑tick timing
  - cxx:
    - bus decay test; one‑growth‑per‑tick test; edge/windowed wiring smoke
    - stress: HD 1920×1080 + Retina/Topographic single‑tick timing (gtest)
    - proximity STEP placeholder test (disabled) until integrated into Region
  - mojo:
    - bus decay test; frozen slots test; one‑growth‑per‑tick test
    - stress: HD 1920×1080 + Retina/Topographic single‑tick execution (timing observed via wall‑clock in script)
  - benchmarking:
    - `scripts/run_stress_bench.sh` runs HD + Retina stress across languages and prints a timing table; docs in `docs/BENCHMARKS.md`

open_items_to_watch:

  - Keep windowed-tract re-attach verified across Java/Mojo as code evolves
  - Maintain “one growth per tick” invariant at region level
  - Ensure `owner` backrefs are set for any new layer types
  - Integrate proximity policy in C++ Region tick; enable STEP tests and parity with Python/Java/Mojo
  - Consider CI matrix for stress script on a fixed runner to track regressions

---END PROJECT MEMORY---

Conventions:
- Python and Mojo: no leading-underscore names. No camelCase names except for class names or struct names.
- Mojo uses struct + fn with typed params.
- Use descriptive variable names. 
- No single/double-character variable names anywhere.
- For Mojo: Do not use let keyword. Use var instead. Mojo does not support let currently.

Goal for this thread:
- Continue development with full parity on automatic growth (Slots→Neurons→Layers→Regions),
  deterministic wiring, and two-phase ticks with bus cooldown semantics.
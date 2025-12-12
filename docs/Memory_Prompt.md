You are Codex 5.2. Your job is to internalize GrowNet so you can implement future changes quickly and safely.

#### **Scope**

- DO NOT modify any files.
- DO NOT do documentation consistency cleanups (already handled).
- Output only a “Readiness Review” and a concise “Memory Transfer Summary.”

Project summary (keep in mind)
GrowNet is a growth-based neural architecture that starts very small and adds capacity only when the data proves it needs to, instead of training one huge fixed network with backprop. Inputs are routed into “slots” (local memory cells) inside each neuron; when a neuron runs out of slots and keeps seeing novelty, it triggers neuron growth (more neurons of the same kind are added), and when layers saturate, the system can grow new layers (and potentially regions in future). Growth is deterministic (no random architecture search), driven by explicit novelty signals with cooldowns and thresholds, with one growth action per region per tick. For 2D data, GrowNet uses windowed wiring (SAME/VALID center rule), dedupes cross-window duplicates, and returns the unique-source count for windowed connections. Newest concepts: KU and BKU (Knowledge Units / Bad Knowledge Units) as evaluation metrics.

#### **Key files** (read in order)

1) docs/READ_ORDER.md
2) docs/DOCS_INDEX.md
3) docs/contracts/grownet.contract.v5.json            (authoritative contract)
4) docs/contracts/grownet.contract.schema.json        (validation)
5) docs/contracts/CONTRACT_RENDER.md                  (human render)
6) docs/GrowNet_Design_Spec_V5.md
7) docs/CODING_STYLE_MUST_READ.md
8) docs/KnowledgeUnits.md and docs/KU_BKU_Evaluation_Protocol.md
Then scan the implementations:
- src/python/
- src/cpp/
- src/java/
- src/mojo/
- src/typescript/
- src/rust/ (if present)

#### Tie-breakers (when something conflicts)

1) grownet.contract.v5.json (public API + invariants)
2) GrowNet_Design_Spec_V5.md (behavioral semantics)
3) CODING_STYLE_MUST_READ.md (naming, clean code, determinism rules)

Hard invariants (must internalize)
- Strict slot capacity: never allocate a new slot when at capacity (except empty bootstrap); set last_slot_used_fallback when blocked.
- Freeze/unfreeze: unfreeze triggers “prefer last slot once” behavior.
- Tick discipline: phase A, phase B, then end_tick; bus.decay does inhibition *= decay, modulation = 1.0, current_step++.
- Neuron growth: fallback streak >= threshold AND cooldown passed ⇒ add one same-kind neuron; copy slot config; share bus; deterministic autowiring.
- Region growth: OR-trigger (avg slots OR % at-cap+fallback) + cooldown; <=1 growth per region per tick; spillover wiring p=1.0 unless policy overrides.
- Windowed wiring: SAME/VALID center rule (floor + clamp); dedupe duplicates; connect_layers_windowed returns unique source count; tract re-attach on source growth.
- PAL determinism: ordered reduction/stable tiling; results stable across worker counts.
- TypeScript note: one growth per layer per tick; supports percentAtCapFallbackThreshold alias.
- Mojo note: no let; explicit .copy() for containers/configs; iterators yield references; avoid file-scope mutable globals.

#### KU / BKU

- KU = correct generalizable structure gained per sample beyond literal memorization.
- BKU = incorrect/harmful generalizations per sample (hallucinations + bias).
- KU/BKU are evaluation concepts; do not assume they are part of RegionMetrics unless contract says so.

#### Tasks (read-only)

1) **Memory Transfer Summary (1–2 pages)**
   - What GrowNet is (invariants + intuition)
   - The Golden Rule and how it maps to slot/neuron/layer/region growth
   - Where each invariant is implemented per language (paths + key classes)

2) **“Where to edit what” cheat-sheet**
   - Slot selection + fallback marking (all languages)
   - Neuron growth trigger + instantiation points
   - Region growth policy trigger + request_layer_growth path
   - Windowed wiring + tract re-attach (center rule + unique-source return)
   - PAL determinism hooks

3) **Risk map (no fixes, just flags)**
   - The top 10 places future edits tend to break parity/determinism (e.g., center mapping, dedupe, bus step clock, growth guardrails)
   - Any places where contract claims require extra care (but do not propose refactors)

#### Deliverable format

- Use markdown headings.
- Keep it actionable and terse.
- Do not write code or patches.
- Do not move or rename files.
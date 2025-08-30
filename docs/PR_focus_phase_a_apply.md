## Familiarize (must run before editing)

You are Codex. First, build a quick mental map of the repo; if anything is missing or renamed, STOP with a precise message.

1) Repo survey
   - Run:
     - `git rev-parse --abbrev-ref HEAD`
     - `ls -la`
     - `readlink -f src/java || true`
     - `rg -n "package ai\\.nektron\\.grownet|class\\s+Region|class\\s+Neuron|class\\s+SlotConfig|class\\s+SlotEngine" -S src/java`
     - `rg -n "class\\s+Region|class\\s+Neuron|SlotConfig|SlotEngine" -S src/python`
     - `rg -n "struct\\s+.*SlotConfig|class\\s+Neuron|SlotEngine" -S src/cpp`
     - `rg -n "struct\\s+SlotConfig|struct\\s+Neuron|slot_engine" -S src/mojo`

2) Read these files (only what you need—avoid dumping full files to stdout):
   - `src/java/ai/nektron/grownet/{Region.java,Neuron.java,SlotConfig.java,SlotEngine.java,Layer.java}`
   - `src/python/{region.py,neuron.py,slot_config.py,slot_engine.py}`
   - `src/cpp/{SlotConfig.h,SlotEngine.h,SlotEngine.cpp,Neuron.h}`
   - `src/mojo/{slot_config.mojo,neuron.mojo,slot_engine.mojo}`
   - `codex/docs/README_Codex.md` (normative guardrails)
   - `docs/GrowNet_Design_Spec_V3.md`
   - `docs/contracts/GrowNet_Contract_v3_master.yaml`

3) Confirm invariants (STOP if any fail)
   - Java is present and is the gold source.
   - `src/java` points to the actual Java tree (symlink OK).
   - Python fields use snake_case and **no leading underscores**.
   - Mojo uses `struct`/`fn`, explicit types, simple style (no clever tricks).
   - Public APIs like `Region.connectLayers`, `Region.bindInput`, `tick/tick2D/tickND` **must not be removed**.
   - “Ports are edges”; 2D uses `tick2D` (`tickImage` may delegate); ND uses `tickND`.

If any invariant or file path is missing, print:  
`PRECONDITION FAILED: <what’s missing and where you looked>` and stop.


# PR: Phase A — Temporal Focus (WRITE TO DISK)

You are Codex (GPT‑5, max reasoning). **Edit files in place and write the changes to disk.**
Do **not** print a unified diff; instead, after you finish, print a short summary list of modified files.

## Rules
- Work in the current repo root.
- Java is gold semantics; mirror patterns in Python/C++/Mojo.
- Do **not** remove public methods; if behavior changes, keep delegating aliases.
- If a target file is missing for a language, **skip that language** gracefully.
- Keep the existing project layout (Java under `src/java` symlink).
- **Write to disk**; do not emit patches.
- After edits, print a bullet list of the files you changed.

## Changes to make

### Java
1. **Add growth scaffolding**
   - Create `src/java/ai/nektron/grownet/growth/GrowthPolicy.java` with conservative defaults (layer and neuron growth knobs, cooldown).
   - Create `src/java/ai/nektron/grownet/growth/GrowthEngine.java` with:
     - `maybeGrow(Region, GrowthPolicy)`: layer-pressure heuristic (avg slots/neuron; if high and below max layer count, add a layer and wire from previous).
     - `maybeGrowNeurons(Region, GrowthPolicy)`: best-effort outlier hook (reflection safe) based on temporal‑focus delta% vs anchor.
   - Both classes must compile without changing Layer/Region public APIs.

2. **Region growth hook**
   - Edit `src/java/ai/nektron/grownet/Region.java`:
     - Add private field `ai.nektron.grownet.growth.GrowthPolicy growthPolicy`.
     - Add `getGrowthPolicy()` and fluent `setGrowthPolicy(GrowthPolicy)` accessors.
     - At the end of `tick(...)`, just before `return`, add a try/catch that calls
       `ai.nektron.grownet.growth.GrowthEngine.maybeGrowNeurons(this, growthPolicy)` if `growthPolicy != null`.
     - Leave an anchor comment somewhere near class top, e.g. `// [GROWNET:ANCHOR::AFTER_METRICS]`.

3. **SlotConfig anchor knobs**
   - Edit `src/java/ai/nektron/grownet/SlotConfig.java`:
     - Add `enum AnchorMode { FIRST, EMA, WINDOW, LAST }` and fields:
       `anchorMode (FIRST default), binWidthPct (10.0), epsilonScale (1e-6), recenterThresholdPct (35.0), recenterLockTicks (20), anchorBeta (0.05), outlierGrowthThresholdPct (60.0), slotLimit (16)`.
     - Add standard getters/setters that clamp sensibly (non‑negative, sane bounds).
     - Do not remove existing fields/factories.

4. **Neuron focus state**
   - Edit `src/java/ai/nektron/grownet/Neuron.java`:
     - Add fields `focusAnchor` (double), `focusSet` (boolean), `focusLockUntilTick` (long) and a `getFocusAnchor()` accessor.

5. **SlotEngine FIRST‑anchor helper**
   - Edit `src/java/ai/nektron/grownet/SlotEngine.java`:
     - Add `int selectOrCreateSlot(Neuron n, double x, SlotConfig cfg)` that:
       - If `!n.focusSet && cfg.getAnchorMode()==FIRST` → set `n.focusAnchor=x; n.focusSet=true`.
       - Compute `deltaPct = 100*|x - focusAnchor| / max(|focusAnchor|, epsilonScale)`.
       - Map to `slotId = floor(deltaPct / max(0.1, binWidthPct))`.
       - Ensure a slot exists in `n.getSlots()`; clamp to `cfg.getSlotLimit()` if at capacity.
     - Keep existing methods intact.

### Python
- Edit `src/python/slot_config.py`: inside `class SlotConfig`, add class attributes
  `anchor_mode="FIRST", bin_width_pct=10.0, epsilon_scale=1e-6, recenter_threshold_pct=35.0, recenter_lock_ticks=20, anchor_beta=0.05, outlier_growth_threshold_pct=60.0, slot_limit=16`.
- Edit `src/python/neuron.py`: in `__init__`, add `focus_anchor=0.0`, `focus_set=False`, `focus_lock_until_tick=0`.
- Edit `src/python/slot_engine.py`: implement `select_or_create_slot(self, neuron, input_value, tick_count=0)` that:
  - Sets anchor if not set and mode is FIRST.
  - Computes `delta_pct` as above; bins by `bin_width_pct`; ensures a slot; clamps if `slot_limit` reached.
  - Returns the `Weight` for that slot. Keep existing methods.

- Add test `src/python/tests/test_temporal_focus.py` with a simple sequence asserting ≥10 slots after feeding `[1.0 … 2.0]` via `Region.tick`.

### C++
- Edit `src/cpp/SlotConfig.h`:
  - Add `enum class AnchorMode { FIRST, EMA, WINDOW, LAST };`
  - Add fields matching Java anchor knobs (with same defaults) including `slotLimit`.
- Edit `src/cpp/Neuron.h`:
  - Add public focus state: `double focusAnchor{0.0}; bool focusSet{false}; long long focusLockUntilTick{0}; double getFocusAnchor() const { return focusAnchor; }`
- Edit `src/cpp/SlotEngine.cpp`:
  - In `selectOrCreateSlot(...)`, implement FIRST‑anchor logic mirroring Java; include `<algorithm>`; clamp to `cfg.slotLimit`.

### Mojo
- Edit `src/mojo/slot_config.mojo`:
  - Add `enum AnchorMode` and fields to mirror Java/Python; `slot_limit: Int = 16`.
- Edit `src/mojo/neuron.mojo`:
  - Add `focus_anchor: Float64 = 0.0`, `focus_set: Bool = False`, `focus_lock_until_tick: Int = 0`.
  - Keep style simple (struct/fn, typed params).

## Output
After writing all edits to disk, print:
- A bullet list of files you changed (relative paths).
- A one‑line note “Phase A (Temporal Focus) applied.”


# CHANGELOG — 2025-09-01

This entry summarizes the code and docs updates completed today:

- PR-10: Spatial windowed wiring polish (deterministic Input2D→Output2D) + docs clarifications
- Java: V4 Temporal Focus default + unified bus decay semantics
- PR-11: Frozen Slots (opt-in per-slot stability) across Python/Java/C++/Mojo

## Highlights

- Deterministic `connectLayersWindowed` on C++ `Region` with clear return semantics and center rule.
- Anchor-based Temporal Focus is now the default in Java `Neuron.onInput`.
- Unified bus decay: inhibition decays multiplicatively (0.90), modulation resets each tick.
- Frozen Slots: per-slot `frozen` flag to lock learning/θ updates while still participating in firing.

## Changes by Area

### Docs

- `docs/SPATIAL_FOCUS.md`
  - Clarified that windowed wiring returns the number of unique source subscriptions (distinct participating source pixels), not raw edge count.
  - Documented even-kernel center rule for `padding="same"` (center via floor, clamped to bounds).
  - Added C++ parity notes for `InputLayer2D → OutputLayer2D` and temporary generic fan-out behavior.

- `docs/STYLE_AND_PARITY.md`
  - Added unified bus semantics: inhibition decays multiplicatively each tick (default 0.90), modulation resets to 1.0.

### C++

- Windowed wiring (spatial helper):
  - Implemented `Region::connectLayersWindowed(...)` with deterministic behavior and safe semantics.
    - `OutputLayer2D` destination: each window connects all participating source pixels to the center output neuron (floor center, then clamp), deduplicating `(srcIdx, centerIdx)` pairs; returns count of unique sources.
    - Non-`OutputLayer2D` destination: deterministic persistent fan-out from each participating source pixel to all destination neurons (temporary stopgap).
  - Safe allocation for `allowedMask` via `size_t(height) * size_t(width)`.
  - Added 64-bit unsigned packing helper for dedupe keys.
  - Clamped window center to the destination shape.
  - Includes updated (`<stdexcept>`, `<unordered_set>`, `<algorithm>`, `<cstdint>`).

- Accessors added:
  - `InputLayer2D.h`: `getHeight()`, `getWidth()`.
  - `OutputLayer2D.h`: `getHeight()`, `getWidth()`.

- Return semantics clarified in declaration:
  - `Region.h`: comment states return is count of unique source subscriptions.

- Smoke test (guarded):
  - `src/cpp/tests/WindowedWiringSmoke.cpp` (compiled with `-DGROWNET_WINDOWED_WIRING_SMOKE`).

- Frozen Slots:
  - `Weight.h`: added `frozen` with `freeze/unfreeze/isFrozen`; `reinforce` and `updateThreshold` respect frozen.
  - `Neuron.h`: track `lastSlotId`; helpers `freezeLastSlot()/unfreezeLastSlot()`.
  - `SlotEngine.cpp`: records `lastSlotId` when selecting slots (uses actual inserted key).

### Java

- Temporal Focus default (V4):
  - `ai/nektron/grownet/Neuron.java`: `onInput` now uses `SlotEngine.selectOrCreateSlot(...)` (anchor-based) and records `lastSlotId`.

- Unified bus decay:
  - `ai/nektron/grownet/LateralBus.java`: added `inhibitionDecay` (default 0.90), `get/setInhibitionDecay`; `decay()` multiplies inhibition and resets modulation.

- Frozen Slots:
  - `ai/nektron/grownet/Weight.java`: added `frozen` with `freeze/unfreeze/isFrozen`; `reinforce`/`updateThreshold` honor frozen state.
  - `ai/nektron/grownet/Neuron.java`: remembers `lastSlotId`; added `freezeLastSlot()/unfreezeLastSlot()`.

### Python

- Frozen Slots:
  - `src/python/weight.py`: added `frozen` with `freeze/unfreeze/is_frozen`; `reinforce`/`update_threshold` honor frozen state.
  - `src/python/neuron.py`: tracks last selected slot (`_last_slot`) for scalar and 2D flows; adds `freeze_last_slot()/unfreeze_last_slot()`.

### Mojo

- Frozen Slots:
  - `src/mojo/weight.mojo`: added `frozen` with freeze/unfreeze/is_frozen; `reinforce`/`update_threshold` honor frozen.
  - `src/mojo/neuron.mojo`: tracks `last_slot_id`; adds `freeze_last_slot()/unfreeze_last_slot()` and records last id at selection.

## Behavior & Compatibility

- Default behavior remains unchanged unless features are explicitly exercised:
  - Windowed wiring now present in C++; return value defined as unique source count.
  - Java neurons adopt anchor-based slotting by default (Temporal Focus V4); increases slot diversity on monotonic ramps.
  - Bus decay unified across languages (inhibition multiplicative decay 0.90; modulation reset), matching Python/C++ tests.
  - Frozen Slots are opt-in; frozen compartments still evaluate firing but skip reinforcement and θ/EMA updates.

## Touched Files (selected)

- Docs: `docs/SPATIAL_FOCUS.md`, `docs/STYLE_AND_PARITY.md`
- C++: `src/cpp/Region.h`, `src/cpp/Region.cpp`, `src/cpp/InputLayer2D.h`, `src/cpp/OutputLayer2D.h`, `src/cpp/Weight.h`, `src/cpp/Neuron.h`, `src/cpp/SlotEngine.cpp`, `src/cpp/tests/WindowedWiringSmoke.cpp`
- Java: `src/java/ai/nektron/grownet/Neuron.java`, `src/java/ai/nektron/grownet/LateralBus.java`, `src/java/ai/nektron/grownet/Weight.java`
- Python: `src/python/weight.py`, `src/python/neuron.py`
- Mojo: `src/mojo/weight.mojo`, `src/mojo/neuron.mojo`

## Test Notes

- C++: build and run the guarded smoke test (`WindowedWiringSmoke.cpp`) to validate windowed wiring return counts.
- Python: existing test suite remains green; no default behavior changes.
- Java/C++/Python: verify inhibition decay if tests/doc examples depend on prior semantics (expected new default is 0.90 decay per tick).


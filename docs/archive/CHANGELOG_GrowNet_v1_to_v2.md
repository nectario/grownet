# CHANGELOG — GrowNet v1 → v2

**Scope:** Unify the neuron contract across languages; add shape‑aware I/O layers and demos; clarify buses and tick phases.

## Major
- **Unified contract** for *every neuron*: `onInput(value, …) -> fired`, `onOutput(amplitude)` (outputs accumulate; others no‑op).
- **Output neurons never propagate** (no `fire`); actuator boundary is explicit.
- **Input & Output single‑slot types** added; image‑ready **InputLayer2D/OutputLayer2D** shipped.
- **Two‑phase tick** documented and mirrored in Region helpers (`tick_image` in all languages).
- **Cross‑language parity** table and method signature notes.

## Minor
- Bus semantics clarified (modulation & inhibition factors, decay).
- Slot saturation target explicit (10,000 hits).
- Defaults specified: `beta=0.01`, `eta=0.02`, `r_star=0.05`, `epsilon_fire=0.01`.
- Demo mains added for Python, Java, C++, Mojo.

## Migration Notes
- Add no‑op `onOutput` to base Neuron (all languages).
- Ensure Layer calls `onOutput` when a neuron fires (before propagation).
- Output layers must call `end_tick()/endTick()` each tick (Region convenience does this).
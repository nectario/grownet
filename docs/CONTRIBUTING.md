# Contributing — Comment Style Guide

This project favors concise, purpose‑driven comments that clarify intent without restating code. As a rule: explain “why” and the contract; keep “what/how” to places where the code is non‑obvious.

Recommended patterns

- Modules/classes: one short sentence on the role and the key contract.
- Public methods/functions: a one‑liner describing inputs/outputs and any invariants.
- Non‑obvious logic: a brief note on the idea or edge case (preferably with a known term from the docs).
- Cross‑language parity: when a construct exists to mirror other languages, say so briefly.

Areas to mention explicitly

- Region ticks: “ports‑as‑edges” model — a tick drives the bound edge once; downstream layers receive activity via wiring.
- SlotEngine: FIRST‑anchor temporal focus; binning knobs (bin_width_pct, epsilon_scale) and slot_limit clamping.
- Weight: T0 imprint + T2/EMA drift; return indicates threshold crossing.
- Buses: LateralBus/RegionBus factors are transient and decay per tick.

Language specifics

- Python: use docstrings (triple‑quoted) for modules/classes/methods; short inline comments where needed.
- Java: use Javadoc for public methods; add short line comments for subtle branches/assumptions.
- C++: prefer brief header comments and one‑liners above non‑obvious functions; avoid over‑explaining.
- Mojo: use `#` comments sparingly; one‑liners at function boundaries are sufficient.

Tone and brevity

- Keep comments crisp (one–two lines). Avoid duplicating names/signatures or restating simple loops.
- Prefer “why” and invariants over narration of every step.

Reference

- See docs/GrowNet_Design_Spec_V4.md for the conceptual background behind ports‑as‑edges, temporal focus, and growth hooks.

# RFC: GrowNet Rust Port — Phase 1

Scope: establish core model, deterministic clocking, strict capacity + fallback, growth scaffolding,
and windowed wiring stubs. Not yet integrated: proximity policy wiring and full event propagation.

## Key invariants
- Two-phase tick; bus decay as spec.
- Slot selection anchor FIRST; 2D packs (row_bin, col_bin) as `r*100000 + c`.
- Strict capacity with bootstrap exception (empty engine may allocate).
- Fallback sets `last_slot_used_fallback`; `unfreeze_last_slot` is one-shot reuse.
- Growth: same-kind neuron; copy config; share bus; p=1.0 spillover when region grows.
- One growth per region per tick enforced via cooldown clock tied to `bus.current_step`.

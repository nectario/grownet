# GrowNet — Rust Port (Phase 1)

This workspace contains the initial Rust port of GrowNet focusing on **core data structures, 
tick discipline, slot selection, strict capacity with deterministic fallback, and growth scaffolding**.

> Invariants preserved:
> - Slots → Neurons → Layers → Region hierarchy
> - Strict capacity + deterministic fallback (`last_slot_used_fallback` as the *only* pressure signal)
> - Fallback-streak + cooldown → **neuron growth** (same kind, copy config, share bus)
> - **One growth per region per tick** at region level
> - Windowed wiring scaffolding with **center rule** and **unique source subscriptions**
> - Two-phase tick and bus decay: inhibition *= decay, modulation = 1.0, current_step += 1
> - Deterministic RNG seeded in `Region`

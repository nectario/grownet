# GrowNet Contract (v5 + addendum v5.1)

This is a **machine-first** contract for GrowNet. The authoritative source is JSON:
- `docs/contracts/grownet.contract.v5.json` (authoritative)
- `docs/contracts/grownet.contract.v5.canonical.json` (canonical, sorted keys)
- `docs/contracts/grownet.contract.schema.json` (validation schema)

## Purpose
Define the cross-language public surface (Python, C++, Java, Mojo, TypeScript, Rust) and the behavioral invariants for slot selection, frozen slots, two-phase ticking, and automatic growth across Slots → Neurons → Layers → Regions.

## Reading rule
When documents disagree:
1. **Contract JSON** (this) for public API + invariants
2. **Design Spec V5** for detailed behavior
3. **Coding Style** for naming + clean code rules

## Key invariants (high signal)
- **Local, event-driven learning** (no backprop).
- **Strict slot capacity**; fallback marking is the pressure signal.
- **Two-phase tick** (A integrate/select/fire, B propagate; then end_tick + bus.decay).
- **Bus decay**: inhibition decays multiplicatively; modulation resets to 1.0; step increments each tick.
- **Growth escalation**: Slots → Neurons → Layers → Regions (bounded and deterministic).
- **One growth per region per tick** (region-level safety invariant).
- **Deterministic autowiring**: mesh rules + tract reattach.
- **Windowed wiring**: SAME/VALID center rule, dedupe, return **unique source count**.

## Evaluation concepts
- **KU** (Knowledge Units): correct generalization per sample beyond literal memorization.
- **BKU** (Bad Knowledge Units): hallucinations + biased/harmful generalizations induced per sample.
- Canonical docs:
  - `docs/KnowledgeUnits.md`
  - `docs/KU_BKU_Evaluation_Protocol.md`

## Types (summary)
This contract defines canonical fields and method signatures for key types:
- SlotConfig, Weight, Neuron, Layer, Tract, Region
- LateralBus, RegionBus, MeshRule, GrowthPolicy
- RegionMetrics

> For full details, consume `grownet.contract.v5.json` directly.

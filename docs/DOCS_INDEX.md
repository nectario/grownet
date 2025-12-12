# GrowNet Documentation Index
_Last updated: 2025-12-12_

This index is the “table of contents” for GrowNet documentation. It is designed for fast onboarding and reliable memory transfer (humans and Codex/GPT alike).

## How to read
- Follow **`docs/READ_ORDER.md`** end-to-end. It is the canonical reading sequence.
- When documents disagree:
  1) **Contract v5** (public API + invariants) wins  
  2) **Design Spec V5** (behavior) wins  
  3) **Coding Style** (naming + clean code rules) wins

## Fast Path
Read these first to get oriented quickly:

1. **Overview & narrative**
   - `docs/What_This_Codebase_is_About_v2.md`
   - `docs/GrowNet_in_Plain_Language_v2.md`
   - `docs/GrowNet_Overview.md`

2. **Golden Rule**
   - `docs/golden_rule.md` *(or the canonical Golden Rule doc in this repo)*
   - `docs/GrowNet_Golden_Rule_In_Plain_English.md` *(if present)*

3. **Tick discipline & determinism (core invariants)**
   - `docs/tick_discipline.md`
   - `docs/autowiring_and_tracts.md`

4. **Focus & Growth cheat-sheets**
   - `docs/FOCUS_AND_GROWTH_CHEATSHEET.md`
   - `docs/GROWTH_CHEATSHEET.md`
   - `docs/2D_Bins_Spatial_Focus.md`

5. **KU / BKU (learning yield)**
   - `docs/KnowledgeUnits.md` *(KU/BKU definition)*
   - `docs/KU_BKU_Evaluation_Protocol.md` *(measurement protocol)*

## Deep Path
Use this path when you need exact semantics and cross-language parity details:

- **Contract & spec**
  - `docs/contracts/GrowNet_Contract_v5_master.yaml`
  - `docs/GrowNet_Design_Spec_V5.md`

- **Growth mechanics**
  - `docs/GROWTH.md`
  - `docs/The_conditions_of_growth_in_simple_terms_for_all_parts.md`
  - `docs/What_is_a_cooldown.md`

- **Spatial focus / wiring**
  - `docs/2D_Bins.md`
  - `docs/2D_Bins_Spatial_Focus.md`
  - `docs/SPATIAL_FOCUS.md`

- **PAL determinism / benchmarking**
  - `docs/introducing_parallelism_concurrency_in_grownet.md`
  - `docs/BENCHMARKS.md`
  - `src/bench/README.md`

- **Reference**
  - `docs/FAQ.md`
  - `docs/GLOSSARY.md`
  - `docs/CODING_STYLE_MUST_READ.md`

## Archive
Anything under `docs/archive/` is intentionally **non-canonical**: old drafts, PR write-ups, chat exports, historical notes, and duplicates. It is kept for traceability, not for onboarding.

## Where to look in code (by language)
- Python: `src/python/`
- C++: `src/cpp/`
- Java: `src/java/`
- Mojo: `src/mojo/`
- TypeScript: `src/typescript/`
- Rust: `src/rust/` *(or the Rust workspace path, if integrated elsewhere)*

## The invariants we protect (quick list)
- Strict slot capacity; fallback marking is the **only** pressure signal.
- Freeze/unfreeze: unfreeze → **prefer last slot once**.
- Two-phase tick discipline; bus decay: inhibition *= decay, modulation = 1.0, step++.
- Neuron growth: fallback streak ≥ threshold and cooldown passed → grow same kind.
- Region growth: OR-trigger (avg slots OR % at-cap+fallback) + cooldown; **≤1 growth per region per tick**; spillover wiring uses **p=1.0**.
- Windowed wiring: SAME/VALID **center rule (floor+clamp)**; dedupe; return **unique source count**; tract re-attach on source growth.
- PAL determinism: ordered reduction / stable tiling; results stable across worker counts.


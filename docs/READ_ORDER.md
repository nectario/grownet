# GrowNet — Reading Order (GPT‑5.2 / Codex memory transfer)

This file defines the **authoritative reading sequence** for internalizing GrowNet quickly and correctly.

## Tie‑breakers (when docs disagree)

1. **contracts/grownet.contract.v5.json** — source of truth for **public APIs** and **cross‑language invariants**.
2. **GrowNet_Design_Spec_V5.md** — source of truth for **behavior** (growth rules, determinism, tick phases).
3. **CODING_STYLE_MUST_READ.md** — source of truth for **style rules** (naming, determinism, clean code).
4. Everything else — helpful guidance, but must not contradict the above.

> **Version rule:** prefer the newest document (e.g., v5 over v3). Older versions belong in docs/archive/.

---

## Fast path (recommended first pass)

Read these in order to load the correct mental model fast:

1) **Overview & narrative context**
   - `What_This_Codebase_is_About_v2.md`
   - `GrowNet_in_Plain_Language_v2.md`
   - `GrowNet_Overview.md`
   - `CONTEXT_GrowNet_Vision.md`
   - `README.md`
   *Why:* big picture, motivation, and non‑expert framing.

2) **The Golden Rule (principle → mechanism)**
   - `GOLDEN_RULE.md`
   - `GrowNet_Golden_Rule_In_Plain_English.md`
   *Why:* anchors the core promise: **“When the world looks truly new, GrowNet makes room.”**

3) **Contract + Design Spec (authoritative)**
   - `contracts/grownet.contract.v5.json`
   - `GrowNet_Design_Spec_V5.md`
   *Why:* defines the public surface and the exact invariants (growth, determinism, tick discipline).

4) **Style, parity, and “don’t break determinism” rules**
   - `CODING_STYLE_MUST_READ.md`
   - `STYLE_AND_PARITY.md`
   *Why:* keeps implementations consistent across **Python / C++ / Java / Mojo / TypeScript / Rust**.

5) **Growth (Slots → Neurons → Layers → Regions)**
   - `GROWTH.md`
   - `GROWTH_CHEATSHEET.md`
   - `FOCUS_AND_GROWTH_CHEATSHEET.md`
   - `CREATION_AND_GROWTH_POINTS.md`
   - `The_conditions_of_growth_in_simple_terms_for_all_parts.md`
   - `What_is_a_cooldown.md`
   *Why:* exact triggers, cooldowns, and the “one growth per region per tick” safety invariant.

6) **Spatial focus / 2D windowed wiring**
   - `SPATIAL_FOCUS.md`
   - `2D_Bins.md`
   - `ANCHOR_GUIDELINES.md`
   - `2D_Bins_Spatial_Focus.md`
   - `ProximityPolicy.md` (optional policy)
   *Why:* FIRST‑anchor 2D binning; SAME/VALID **center mapping**; **dedupe semantics**; return value is **unique source count**; and `Tract.attach_source_neuron(...)` / `attachSourceNeuron(...)` on source growth.

7) **Parallelism (PAL) + determinism**
   - `Parallelism_Concurrency_Abstraction.md`
   - `introducing_parallelism_concurrency_in_grownet.md`
   - `BENCHMARKS.md`
   *Why:* ordered reductions + stable tiling so results match across worker counts/devices.

8) **Quality gates**
   - `TESTING.md`
   - `Readiness_autogrowth_what_complete_looks_like.md`
   *Why:* defines “done” for parity and regression safety.

9) **Learning yield metrics (new)**
   - `Knowledge_Units_in_GrowNet.md`
   - `KU_BKU_Evaluation_Protocol.md`
   *Why:* KU/BKU are a language‑agnostic way to talk about **per‑sample learning yield** and **bad knowledge** (hallucination/bias) separately.

---

## Deep path (second pass)

These are “operator docs” and are recommended once the fast path is loaded:

10) **Hands‑on engineering guides**
   - `GrowNet_Quick_Start_for_Engineers.md`
   - `GrowNet_Tutorial.md`
   - `GrowNet_API_One_Pager.md`
   - `DEMO_RUN.md`

11) **Debugging and interpretation**
   - `GrowNet_Debugging.md`
   - `INTERPRETATION_GUIDE.md`
   - `GLOSSARY.md`
   - `FAQ.md`

12) **Contribution workflow**
   - `CONTRIBUTING.md`
   - `CHANGELOG.md`

---

## Code reading pointers (after docs)

Once the above is read, review code per language:

- **Python:** `src/python/`
- **C++:** `src/cpp/`
- **Java:** `src/java/`
- **Mojo:** `src/mojo/`
- **TypeScript:** `src/typescript/`
- **Rust:** `src/rust/`

Then review benchmarks + stress harness:

- `src/bench/`
- scripts/ (if present in your tree)
- `BENCHMARKS.md`

---

## Stop rules

- If any README/tutorial disagrees with the contract/spec, **contract + design spec win**.
- If any doc implies non‑determinism or “random growth,” it is stale—fix or archive it.
- If any doc references files that no longer exist, update the references immediately.

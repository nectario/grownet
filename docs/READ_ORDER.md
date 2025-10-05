# GrowNet – Reading Order (authoritative)

> **When documents disagree:** the **Contract v5** and the **Design Spec V5** win for public APIs and behavior.  
> **Style & determinism:** Coding style, naming, and determinism/growth invariants are **non-negotiable** across languages.  
> **Version rule:** prefer the newest version (e.g., V5 over V4), treat older ones as history only.

---

## Reading sequence (with “why”)

1) **Overview & narrative context**  
   - `What_This_Codebase_is_About_v2.md`  
   - `GrowNet_in_Plain_Language_v2.md`  
   - `GrowNet_Overview.md`  
   *Why:* the “why” and the big picture for non-experts, PMs, and PR notes.

2) **Golden Rule (principle → behavior)**  
   - `golden_rule.md`  
   - `GrowNet_Golden_Rule_In_Plain_English.md`  
   *Why:* anchors the line — **“When the world looks truly new, GrowNet makes room.”** Maps novelty → targeted, bounded growth at each rung (Slot → Neuron → Layer → Region).

3) **Tick & deterministic wiring fundamentals**  
   - `tick_discipline.md`  
   - `autowiring_and_tracts.md`  
   *Why:* two-phase clock (A then B → end-tick + decay) and deterministic wiring (mesh rules; windowed tracts; re-attach on source growth).

4) **Language parity & style**  
   - `language_parity_and_style.md` *(if present)*  
   - `CODING_STYLE_MUST_READ.md`, `STYLE_AND_PARITY.md`  
   *Why:* align naming, determinism, and public API shapes before reading code.

5) **Growth (how & when)**  
   - `GROWTH.md`  
   - `The_conditions_of_growth_in_simple_terms_for_all_parts.md`  
   - `What_is_a_cooldown.md`  
   - `GROWTH_CHEATSHEET.md`  
   *Why:* strict slot capacity + deterministic fallback; freeze/unfreeze (prefer once); **fallback streak + cooldown ⇒ same-kind neuron growth**; region OR-trigger (avg-slots or % at-cap+fallback) with cooldown; **≤1 region growth per tick**; spillover **p = 1.0**.

6) **Spatial Focus / 2D windowed wiring**  
   - `2D_Bins.md`  
   - `2D_Bins_Spatial_Focus.md`  
   - `SPATIAL_FOCUS.md`  
   *Why:* FIRST-anchor 2D binning; SAME/VALID **center rule (floor + clamp)**; cross-window dedupe; **return = unique source count**; `Tract.attachSourceNeuron(...)` on source growth.

7) **Parallelism & determinism (PAL)**  
   - `introducing_parallelism_concurrency_in_grownet.md`  
   - `BENCHMARKS.md`  
   *Why:* ordered reduction & stable tiling so results match across worker counts/devices.

8) **Testing & “done” checklist**  
   - `TESTING.md` *(if present)*  
   - `Readiness_autogrowth_what_complete_looks_like.md` *(if present)*  
   *Why:* what to run, env toggles (delivered events, spatial metrics), and exactly what “complete” means for growth parity.

9) **Contract & Design (source of truth)**  
   - `contracts/GrowNet_Contract_v5_master.yaml`  
   - `GrowNet_Design_Spec_V5.md`  
   *Why:* public surfaces + behavior spec. Use these to resolve any doc drift.

10) **Demos & bench**  
    - `DEMO_RUN.md`  
    - `src/bench/README.md`  
    *Why:* quick validation paths (focus, windowed wiring, growth smoke).

11) **FAQ / Cheatsheets**  
    - `FAQ.md`  
    - `FOCUS_AND_GROWTH_CHEATSHEET.md`

12) **Changelogs / Migration notes / PR packs**  
    - `CHANGELOG.md`, `MIGRATION_NOTES.md`  
    - `PRs/*`, `changelog/*`

---

## Cross-document invariants (pin these)

- **Windowed wiring return:** *unique source count* (deduped), **not** raw edges.  
- **Center rule:** SAME/VALID with **floor + clamp** centers.  
- **Strict slot capacity & fallback:** fallback is the **only** pressure flag; allow empty-bootstrap exception.  
- **Freeze/unfreeze:** `freeze_last_slot()`; `unfreeze_last_slot()` → *prefer last slot once*.  
- **Neuron growth:** consecutive fallback streak ≥ `fallback_growth_threshold` **and** cooldown passed → grow **same kind**; **copy slot config**; **share bus**; deterministic (mesh-rule) rewiring.  
- **Region growth (OR-trigger):** `avg_slots_threshold` **or** `percent_at_cap_fallback_threshold` + cooldown; **≤1 growth per region per tick**; spillover **p = 1.0**.  
- **Bus decay:** inhibition *= decay; modulation = 1.0; `current_step += 1`.  
- **PAL determinism:** ordered reductions; stable tiling; identical results across worker counts.  
- **TypeScript-specific:** one growth **per layer per tick**; `percentAtCapFallbackThreshold` alias supported.  
- **Mojo-specific:** no `let`; use `var`; **explicit `.copy()`** for containers/config; iterators yield references; avoid file-scope mutable globals.

---

## Stop rules (tie-breakers)

- **Version preference:** prefer V5 over V4; read older versions for history only.  
- **Contract vs. docs:** when procedure notes or READMEs conflict with Contract/Design Spec, **Contract (signatures)** + **Design Spec (behavior)** win.  
- **Deprecated examples:** if any example contradicts `GROWTH.md` or `SPATIAL_FOCUS.md`, follow those two.

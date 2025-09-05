> **Rule of thumb:** when two versions exist (e.g., V4 vs V5), read the **newest** (highest version) and treat the older one as historical context only.

------

## The reading sequence (top → down)

1. **Coding style & parity first (short)**
   - `CODING_STYLE_MUST_READ.md` and `STYLE_AND_PARITY.md`
      *Why:* norms Codex must follow (no leading underscores in public Python/Mojo, `struct`+`fn` in Mojo, no 1–2 char names, deterministic RNG, doc rules).
2. **Big-picture design**
   - `GrowNet_Design_Spec_V5.md` *(or)* `GrowNet_Design_Spec_V4.md`
      *Why:* end-to-end architecture (Region/Layer/Neuron/Slot), two-phase ticks, focus, growth, windowed wiring. Use V5 if present.
3. **Authoritative API surface**
   - `GrowNet_Contract_v5_master.yaml` *(or)* `GrowNet_Contract_v4_master.yaml`
      *Why:* public methods, fields, naming per language; the source of truth for signatures.
4. **Growth (how + when)**
   - `GROWTH.md`
      *Why:* strict slot capacity + fallback, frozen slots, **fallback streak** → neuron growth, layer/region growth, cooldowns, deterministic auto-wiring.
5. **Spatial Focus / Windowed wiring**
   - `SPATIAL_FOCUS.md`
      *Why:* 2D bins, VALID/SAME padding, **center rule (floor + clamp)**, **return = unique source subscriptions**, tract re-attachment on growth.
6. **Testing & invariants**
   - `TESTING.md`
      *Why:* how to run tests, special env flags (e.g., delivered events, spatial metrics), what “pass” means.
   - *(If present)* `Readiness_autogrowth_what_complete_looks_like.md`
      *Why:* the exact **checklist** Codex must satisfy/verify (slots→neurons→layers→region).
7. **Project overview (context)**
   - `What_this_codebase_is_about.md` *(or)* `PROJECT_OVERVIEW.md`
      *Why:* narrative “why” + terminology; helps Codex write better PR messages.
8. **FAQ / Cheatsheets**
   - `FAQ.md` *(and)* `FOCUS_AND_GROWTH_CHEATSHEET.md` (if present)
      *Why:* quick clarifications on ticks, buses, frozen slots, cooldowns, growth order.
9. **Demo / Runbooks**
   - `DEMO_RUN.md` *(or)* `Demos.md`
      *Why:* how to exercise focus, windowed wiring, growth; useful for Codex to validate patches.
10. **PR & CR packs (if you plan to drive Codex via change requests)**

- `codex/PR_*.md` *(in docs root or codex/docs)*
- `codex/cr/PHASE_A.yaml`, `codex/cr/PHASE_B.yaml`, and individual `CR-*.yaml`
   *Why:* procedural instructions Codex can apply; read after the spec/contract so it understands *why* each change exists.

1. **Changelogs / Migration notes**

- `CHANGELOG.md` *and* `MIGRATION_NOTES.md`
   *Why:* highlights semantic shifts (e.g., strict slot capacity, fencepost fixes in windowed wiring).

1. **Language-specific READMEs (if present)**

- `README_Java.txt`, `README_Cpp.txt`, `README_Mojo.md`, `README_Python.md`
   *Why:* build/run instructions Codex needs to compile and test locally.

------

## Simple “stop rules” for Codex

- **Version preference:** prefer `*_V5.*` over V4 (read V4 only if V5 missing or for history).
- **Conflicts:** when doc and contract disagree, **contract wins** for signatures; **design spec** wins for behavior.
- **Deprecated notes:** if a README contradicts `GROWTH.md` or `SPATIAL_FOCUS.md`, follow those two docs (they’re current).

------

## Why this order works

- Codex learns **style** and **parity rules** first → fewer noisy diffs.
- Then the **design** and **contract** give it the “what” and “how”.
- **Growth** and **Spatial** detail the tricky parts.
- **Testing** and the **readiness checklist** tell Codex how to **prove** it’s correct.
- The **overview, FAQ, demos** improve patch rationale and commit messages.
- Finally, **PR/CR packs** give it procedural steps to apply the changes safely.


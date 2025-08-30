# GrowNet Codex Pack

This pack turns GrowNet refactors into **deterministic, auditable change-requests** (CRs) for Codex CLI.
It captures the **vision** (biologically inspired, slot-based, growth-oriented), the **style rules**, and **step-by-step CRs** for:

- **Phase A**: Temporal Focus (anchor-based slotting + neuron growth hook + tests)
- **Phase B**: Spatial Focus (2D spotlight mask + tests)

## How to apply

```bash
# Dry-run
codex apply codex/cr/PHASE_A.yaml --dry-run
# Apply
codex apply codex/cr/PHASE_A.yaml
# Then spatial focus
codex apply codex/cr/PHASE_B.yaml
```

You can also run individual CRs (see `codex/cr/*.yaml`).

## Order of operations
1. `CR-BOOT` — health checks and anchors.
2. `CR-A-01..05` — Temporal Focus.
3. `CR-B-01..02` — Spatial Focus.

## Safety rails
- Every CR has **preconditions** and **postconditions**.
- No public methods are removed; where behavior shifts, **delegating aliases** are kept.
- Language styles enforced (Python snake_case, Mojo `struct` + `fn` + typed params).
- Java remains the **gold** semantics.

See `INTERPRETATION_GUIDE.md` for how Codex should interpret CR YAMLs.

# Contract Enforcement (Phase 1)

## What’s enforced

- Contract JSON validates against `docs/contracts/grownet.contract.schema.json`.
- Canonical contract sync is enforced via `docs/contracts/grownet.contract.v5.canonical.json`.
- `docs/READ_ORDER.md` references are validated (no missing files; no `docs/archive` refs).
- Phase‑1 API drift is detected via conservative “signature presence” scans across languages (no AST parsing).
- Phase‑1 parity smoke runs existing tests (or skips when toolchains aren’t available):
  - Bus decay semantics (`inhibition *= decay`, `modulation = 1.0`, `current_step += 1`)
  - Windowed wiring return semantics (unique source count + dedupe + center rule)
  - Region growth cap (≤ 1 layer growth per tick)

## What remains TODO (Phase 2+)

- AST‑based API drift checks (per language), including parameter/return types and enums.
- Contract‑driven codegen stubs (or compile‑time conformance) where appropriate.
- Broader invariant coverage: strict slot capacity + fallback marking, freeze/unfreeze “prefer once”, tract re‑attach on source growth, PAL ordered reduction determinism.
- Contract‑to‑docs ref validation for contract `canonicalDocRefs` (currently intentionally not enforced).
- CI expansion to run C++/Rust parity reliably (toolchain + dependency strategy).

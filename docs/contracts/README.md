# Contract: machine-first format

## Files
- `grownet.contract.v5.json` — authoritative contract (JSON).
- `grownet.contract.v5.canonical.json` — canonical/sorted JSON for stable diffs and hashing.
- `grownet.contract.schema.json` — JSON Schema (Draft 2020-12) for validation.
- `CONTRACT_RENDER.md` — human-readable overview rendered from the JSON contract.

## Why JSON
GrowNet's contract is primarily consumed by automation and AI tooling:
- unambiguous parsing across languages
- stable canonicalization and hashing
- straightforward schema validation
- easier code generation and parity checking

## Suggested CI checks (recommended)
1) Validate JSON against schema  
2) (Optional) Generate/verify canonical JSON  
3) (Optional) Run contract-driven parity tests per language


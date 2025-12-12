# PR-21 & PR-22 Changes

This bundle applies the next steps after PR-18/19/20:

## PR-21 (strict short-identifier cleanup)
- Updated `scripts/lint/check_short_identifiers.py` to **ban all** 1–2 character identifiers (no allowlist).
- Searched non-core modules (`tests`, `demos`, `examples`, `scripts`, `tools`, `bench`) and renamed short identifiers to descriptive names across Python, Mojo, Java, and C++ sources.
- Updated `CODING_STYLE_MUST_READ.md` language to state: **No single- or double-character identifiers anywhere, including loops.**

## PR-22 (edge enumeration helpers and tests)
- **Mojo**: `src/mojo/tests/edge_enumeration.mojo` includes an edge enumeration helper and a test (`test_center_edges_are_deduped`) asserting windowed-center dedupe for OutputLayer2D.
- **Java**: `src/test/java/ai/nektron/grownet/EdgeEnumerationTests.java` enumerates outgoing synapses and asserts dedupe.
- **C++**: `tests/edge_enumeration_test.cpp` (GTest) does the same; adjust includes/getters as needed if your API names differ.

> Notes:
> - If any tests fail to compile due to slightly different method names (e.g., getters on `Synapse` or layer construction helpers), search for the `// adjust if ... differs` comments and tweak accordingly. No production code changes were required for PR-22.
> - If you want the short-identifier linter to check **only** production code, scope it in your CI to `src/**`. Current configuration will scan all `*.java`, `*.{c,cc,cxx,cpp,h,hpp}` files by default.

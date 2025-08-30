# ANCHOR GUIDELINES

Add **stable comment anchors** where Codex may need to insert code in the future.
Example:
  // [GROWNET:ANCHOR::AFTER_METRICS]

Prefer anchors close to return statements or aggregation points (e.g., metrics aggregation),
so Codex can deterministically insert hooks (growth, logging) without brittle regexes.

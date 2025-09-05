You are joining an ongoing AI Research project called GrowNet (NeurIPS-bound).
Please internalize the content of the following memory block and use it as the
authoritative context for this conversation:

---BEGIN PROJECT MEMORY---
[Paste the entire contents of PROJECT_MEMORY.md here]
---END PROJECT MEMORY---

Conventions:
- Python and Mojo: no leading-underscore names. No camelCase names except for class names or struct names.
- Mojo uses struct + fn with typed params.
- No single/double-character variable names anywhere.

Goal for this thread:
- Continue development with full parity on automatic growth (Slots→Neurons→Layers→Regions),
  deterministic wiring, and two-phase ticks with bus cooldown semantics.
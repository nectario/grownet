# Mojo setup / debug notes

- Recommended: `pip install mojo==0.25.6` (or pin via Pixi).
- Enable crash stack traces during CI runs:
  - env: `MOJO_ENABLE_STACK_TRACE_ON_ERROR=1`
  - build: `mojo build -debug-level=line-tables`

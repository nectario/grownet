# Mojo 0.25.x Setup (GrowNet)

- Install: `pip install mojo==0.25.6`  (or use Pixi: `pixi add "mojo=0.25.6"`)
- VSCode extension: use the single merged Mojo extension (stable/nightly unified).
- Optional CPU crash stacks: set `MOJO_ENABLE_STACK_TRACE_ON_ERROR=1` and build with `mojo build -debug-level=line-tables`.

> We use **explicit `.copy()`** for containers and config structs in Mojo. Avoid implicit copies and `let`; prefer `var` and the standard argument conventions (`read/mut/var/out/deinit`).

# GrowNet · Mojo port (aligned to current Python/Java specs)

This folder contains a **conservative** Mojo implementation mirroring the current
Python design (snake_case API), with these Mojo-specific adjustments:

- All functions/methods are declared with `fn`.
- Function parameters are **fully typed**.
- Intentionally avoids exotic features; only `struct`, `fn`, `var/let`, basic lists/dicts are used.

> Note: Mojo evolves quickly. This code targets the stable subset in the public docs.
> You can run individual files with the `mojo` CLI or stitch them into a package as needed.

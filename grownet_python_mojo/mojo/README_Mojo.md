# GrowNet Mojo Mirror (minimal)

This directory contains a conservative, typed Mojo mirror of the Python API.
It sticks to simple `struct`/`class` plus `fn` methods with explicit types.
The implementation is intentionally thin so it stays compatible with
frequent Mojo language/stdlib updates.

Start from `region.mojo` and `region_metrics.mojo`.  The semantics mirror the
Python `region.py` and `region_metrics.py` (snake_case in Python; `fn`/typed in Mojo).

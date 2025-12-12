# PR: Mojo 0.25 migration (explicit copies, no `let`)

This PR makes purely mechanical updates to the Mojo code:
- Replace `let` with `var` (current toolchain).
- Make `seed.slot_cfg` an **explicit copy** in neuron growth (`try_grow_neuron`).
- In spatial metrics helpers, ensure any local `chosen` frame uses `img.copy()` (no aliasing).

Behavior is unchanged. All wiring, growth, and tick semantics remain as in the V5 spec.

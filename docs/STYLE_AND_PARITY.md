# STYLE & PARITY — Rules Codex must enforce

- **Java**: source of truth; public surfaces match the contract.
- **C++**: mirror signatures; use smart pointers consistently; throw std::out_of_range on index errors.
- **Python**: snake_case across functions/methods; **fields do not start with `_`**.
- **Mojo**: `struct` instead of class; `fn` for functions; explicit parameter/return types; no clever tricks.

- Region API across languages must include: addLayer / connectLayers / bindInput / bindInput2D / bindInputND /
  tick / tick2D / tickND / prune / getName / getLayers / getBus.

- Metrics: `RegionMetrics` with helpers (`incDeliveredEvents/addSlots/addSynapses`) only—no direct field pokes.

- Ports are **edges**: bind creates/ensures an edge layer; tick2D/tickND require an appropriate edge bound to the port.

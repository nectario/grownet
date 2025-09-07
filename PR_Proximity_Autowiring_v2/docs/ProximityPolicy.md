# Proximity Autowiring Policy — Developer Notes

- Runs after Phase‑B and before end_tick/bus.decay.
- Deterministic layout units: grid_spacing=1.2, layer_spacing=4.0 (defaults).
- Spatial hash cell size equals proximity_radius; near() returns candidate buckets; engine filters by Euclidean distance.
- Directed edges; mesh rules recorded for cross‑layer edges if enabled (so future growth inherits wiring).
- Probabilistic modes (LINEAR/LOGISTIC) require a seeded Region RNG; STEP does not.
- No core fields added; sidecar policy only.

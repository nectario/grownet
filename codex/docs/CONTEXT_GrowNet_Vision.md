# CONTEXT — GrowNet Vision (Temporal & Spatial Focus)

**GrowNet** is a biologically inspired, event-driven neural fabric. Each neuron hosts **slots** (thresholded sub-units).
Learning is local (no backprop), modulated by **lateral buses** (inhibition & modulation).

## Temporal Focus (any dimension)
- Each neuron maintains a **focus anchor** `a`. Slot selection uses **percent-delta vs anchor**:
  Δ% = 100 * |x - a| / max(|a|, ε), then bin into fixed-size percent bins.
- Modes: FIRST, EMA, WINDOW, LAST (FIRST by default).
- **Growth trigger**: if slots are at capacity and Δ% exceeds a threshold (outlier), spawn a **sibling neuron** (anchor at current x).

## Spatial Focus (≥2D, but generalizable)
- In shape-aware input layers (2D/ND), compute a **salience mask** (e.g., abs value or contrast).
- Select top-k salient elements (sticky/hysteretic), build a **spotlight mask** (Gaussian falloff),
  and **multiply** inputs before they hit neurons.
- This directs energy to salient regions; Temporal Focus organizes representation there over time.

## Growth policy
- **Slot**: create until `slot_limit`.
- **Neuron**: if outlier & at capacity, spawn sibling (respect per-layer budgets/cooldowns).
- **Layer**: when a layer accumulates blocked neuron growth or high outlier pressure, add a layer (wire from source).
- **Region**: same principle at macro scale (future).


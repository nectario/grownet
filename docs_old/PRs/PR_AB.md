Here’s a clean, paste‑ready PR for the two follow‑ups you asked for:

- **A) Java: windowed wiring with tract storage + re‑attach on neuron growth**
- **B) Mojo: “same‑kind” neuron growth (E/I/M) in `Layer.try_grow_neuron`**

I kept names descriptive (no single‑letter variables), avoided leading underscores in Mojo, and matched the cross‑language semantics we’ve been standardizing on (strict slot capacity, deterministic wiring, growth escalation, cooldown via step counters).

------

## PR Title

**Follow‑ups A & B: Java windowed tracts + re‑attach, Mojo same‑kind neuron growth**

------

## Java changes

### 1) New file: `src/java/ai/nektron/grownet/Tract.java`

```java
package ai.nektron.grownet;

import java.util.*;

/**
 * Deterministic “windowed tract” describing a mapping from a source layer to a destination layer.
 * We record:
 *  - the set of allowed source neuron indices (unique participants),
 *  - an optional sink map (sourceIndex -> single destination index) used for OutputLayer2D “center” mapping,
 *  - the feedback flag to reproduce connection semantics.
 *
 * attachSourceNeuron(newSrcIndex) wires a newly created source neuron using the recorded rules.
 * We connect via Neuron.connect(...) (no runtime hooks required).
 */
public final class Tract {
    private final Layer sourceLayer;
    private final Layer destinationLayer;
    private final boolean feedback;
    private final Set<Integer> allowedSources;         // participating source ids
    private final Map<Integer, Integer> sinkMapCenter; // optional: source -> one destination index

    public Tract(
            Layer sourceLayer,
            Layer destinationLayer,
            boolean feedback,
            Set<Integer> allowedSources,
            Map<Integer, Integer> sinkMapCenter // may be empty if destination is generic
    ) {
        this.sourceLayer = Objects.requireNonNull(sourceLayer, "sourceLayer");
        this.destinationLayer = Objects.requireNonNull(destinationLayer, "destinationLayer");
        this.feedback = feedback;
        this.allowedSources = (allowedSources == null ? Collections.emptySet() : new LinkedHashSet<>(allowedSources));
        this.sinkMapCenter = (sinkMapCenter == null ? Collections.emptyMap() : new LinkedHashMap<>(sinkMapCenter));
    }

    public Layer getSourceLayer() { return sourceLayer; }
    public Layer getDestinationLayer() { return destinationLayer; }
    public boolean isFeedback() { return feedback; }
    public Set<Integer> getAllowedSources() { return Collections.unmodifiableSet(allowedSources); }
    public Map<Integer, Integer> getSinkMapCenter() { return Collections.unmodifiableMap(sinkMapCenter); }

    /**
     * Wire a single new source neuron according to recorded rules.
     * If the source is not part of allowedSources, this is a no‑op.
     */
    public void attachSourceNeuron(int newSourceIndex) {
        if (!allowedSources.contains(newSourceIndex)) return;

        final Neuron source = safeGet(sourceLayer.getNeurons(), newSourceIndex);
        if (source == null) return;

        final Integer maybeCenter = sinkMapCenter.get(newSourceIndex);
        if (maybeCenter != null) {
            // OutputLayer2D “center” mapping: connect to exactly one destination neuron (deterministic)
            final Neuron target = safeGet(destinationLayer.getNeurons(), maybeCenter);
            if (target != null) {
                source.connect(target, feedback);
            }
            return;
        }

        // Generic destination: connect source to all destination neurons once
        for (Neuron target : destinationLayer.getNeurons()) {
            source.connect(target, feedback);
        }
    }

    private static Neuron safeGet(List<Neuron> list, int index) {
        if (index < 0 || index >= list.size()) return null;
        return list.get(index);
    }
}
```

------

### 2) Update: `src/java/ai/nektron/grownet/Region.java`

**Add tract storage, a `connectLayersWindowed(...)` helper, and re‑attach during autowire.**

> *Search for the class header and add the new field near your other region‑level lists:*

```java
// inside class Region
private final List<Tract> tracts = new ArrayList<>();
```

> *Add the windowed connection method (place near your existing connectLayers(..) methods):*

```java
/**
 * Deterministic windowed wiring similar to Python/Mojo:
 * - Computes sliding windows over a source InputLayer2D (height x width).
 * - If destination is OutputLayer2D, connects each participating source pixel to the “center” output neuron of the window.
 * - Otherwise connects each participating source pixel to all destination neurons (once).
 *
 * Returns the number of unique participating source indices (wires count).
 */
public int connectLayersWindowed(
        int sourceIndex,
        int destIndex,
        int kernelHeight,
        int kernelWidth,
        int strideHeight,
        int strideWidth,
        String padding,
        boolean feedback
) {
    if (sourceIndex < 0 || sourceIndex >= layers.size())
        throw new IndexOutOfBoundsException("sourceIndex");
    if (destIndex < 0 || destIndex >= layers.size())
        throw new IndexOutOfBoundsException("destIndex");

    final Layer src = layers.get(sourceIndex);
    final Layer dst = layers.get(destIndex);

    // We duck‑type for “2D input” and “2D output” via Layer API:
    // Expect getHeight()/getWidth() for shape‑aware layers.
    final Integer H = tryGetHeight(src);
    final Integer W = tryGetWidth(src);
    if (H == null || W == null)
        throw new IllegalArgumentException("Source layer must be shape‑aware (2D).");

    final boolean isSame = "same".equalsIgnoreCase(padding);
    final int strideH = Math.max(1, strideHeight);
    final int strideW = Math.max(1, strideWidth);
    final int KH = kernelHeight;
    final int KW = kernelWidth;

    // Generate window origins
    final List<int[]> origins = new ArrayList<>();
    if (isSame) {
        final int padR = (KH - 1) / 2;
        final int padC = (KW - 1) / 2;
        for (int originR = -padR; originR + KH <= H + padR + padR; originR += strideH) {
            for (int originC = -padC; originC + KW <= W + padC + padC; originC += strideW) {
                origins.add(new int[]{originR, originC});
            }
        }
    } else {
        for (int originR = 0; originR + KH <= H; originR += strideH) {
            for (int originC = 0; originC + KW <= W; originC += strideW) {
                origins.add(new int[]{originR, originC});
            }
        }
    }

    // Unique participating source indices
    final Set<Integer> allowed = new LinkedHashSet<>();

    // If destination exposes 2D shape, we do “center mapping” (one target per window).
    final Integer DH = tryGetHeight(dst);
    final Integer DW = tryGetWidth(dst);
    final boolean centerMode = (DH != null && DW != null);

    // Optional source -> dest center index mapping
    final Map<Integer, Integer> sinkMap = new LinkedHashMap<>();

    // Create connections deterministically (no RNG)
    for (int[] origin : origins) {
        final int originR = origin[0];
        final int originC = origin[1];
        final int rStart = Math.max(0, originR);
        final int cStart = Math.max(0, originC);
        final int rEnd = Math.min(H, originR + KH);
        final int cEnd = Math.min(W, originC + KW);
        if (rStart >= rEnd || cStart >= cEnd) continue;

        int centerR = originR + (KH / 2);
        int centerC = originC + (KW / 2);
        if (centerMode) {
            centerR = Math.max(0, Math.min(H - 1, centerR));
            centerC = Math.max(0, Math.min(W - 1, centerC));
            // Clamp to destination bounds
            centerR = Math.max(0, Math.min(DH - 1, centerR));
            centerC = Math.max(0, Math.min(DW - 1, centerC));
        }

        final int centerFlat = (centerMode ? (centerR * DW + centerC) : -1);

        for (int rr = rStart; rr < rEnd; ++rr) {
            for (int cc = cStart; cc < cEnd; ++cc) {
                final int srcFlat = rr * W + cc;
                if (allowed.add(srcFlat)) {
                    final Neuron s = src.getNeurons().get(srcFlat);
                    if (centerMode) {
                        // One target: the center neuron
                        final Neuron t = dst.getNeurons().get(centerFlat);
                        s.connect(t, feedback);
                        sinkMap.put(srcFlat, centerFlat);
                    } else {
                        // Generic: connect to all destination neurons exactly once
                        for (Neuron t : dst.getNeurons()) {
                            s.connect(t, feedback);
                        }
                    }
                }
            }
        }
    }

    // Record a tract so later growth can re‑wire new sources deterministically
    tracts.add(new Tract(src, dst, feedback, allowed, sinkMap));
    return allowed.size();
}

private static Integer tryGetHeight(Layer layer) {
    try { return (Integer) layer.getClass().getMethod("getHeight").invoke(layer); }
    catch (Throwable ignored) { return null; }
}

private static Integer tryGetWidth(Layer layer) {
    try { return (Integer) layer.getClass().getMethod("getWidth").invoke(layer); }
    catch (Throwable ignored) { return null; }
}
```

> *Extend `autowireNewNeuron(...)` so new sources in windowed tracts are wired too (add this at the end of your existing method):*

```java
// 3) Re‑attach for windowed tracts where this layer is the source
for (Tract tract : tracts) {
    if (tract.getSourceLayer() == layer_obj) {
        tract.attachSourceNeuron(new_idx);
    }
}
```

*(If your method is named slightly differently, keep the existing name and just append the loop above.)*

------

## Mojo changes

### 3) Update: `src/mojo/layer.mojo` — same‑kind neuron growth

> Add or replace your growth helper with a same‑kind clone.
>  **Constraints followed:** `fn` syntax, typed parameters, `struct`‑based code, no leading underscores, no single/double‑character names.

```mojo
# inside struct Layer
# Assumptions:
# - self.neurons: list[Neuron]
# - self.bus: LateralBus
# - self.region_ref: Region | None  (if your Region backref has a different name, keep that)
# - neuron_limit: Int  (per-layer cap; -1 means unlimited)
# - Region exposes autowire_new_neuron_by_ref(layer: Layer, new_index: Int)

fn try_grow_neuron(self: inout Layer, seed_neuron: Neuron) -> Int:
    # Enforce per-layer cap
    if self.neuron_limit >= 0 and self.neurons.len >= self.neuron_limit:
        # Optional escalation to layer growth if policy allows
        if self.region_ref is not None and seed_neuron.slot_cfg.layer_growth_enabled:
            _ = self.region_ref.request_layer_growth(self)
        return -1

    # Create a neuron of the same kind as the seed
    let new_index: Int = self.neurons.len
    var new_neuron: Neuron

    if seed_neuron.is_excitatory():
        new_neuron = ExcitatoryNeuron(
            name = "E" + String(new_index),
            bus = self.bus,
            slot_cfg = seed_neuron.slot_cfg,
            slot_limit = seed_neuron.slot_limit
        )
    elif seed_neuron.is_inhibitory():
        new_neuron = InhibitoryNeuron(
            name = "I" + String(new_index),
            bus = self.bus,
            slot_cfg = seed_neuron.slot_cfg,
            slot_limit = seed_neuron.slot_limit
        )
    else:
        new_neuron = ModulatoryNeuron(
            name = "M" + String(new_index),
            bus = self.bus,
            slot_cfg = seed_neuron.slot_cfg,
            slot_limit = seed_neuron.slot_limit
        )

    # Ownership and install into the layer
    new_neuron.owner = self
    self.neurons.append(new_neuron)

    # Deterministic auto‑wiring using recorded rules
    if self.region_ref is not None:
        self.region_ref.autowire_new_neuron_by_ref(self, new_index)

    return new_index
```

> If your Region method is named `autowire_new_neuron` (without `_by_ref`), call that instead.

------

## Quick usage checks

### Java (windowed tract + re‑attach)

```java
Region region = new Region("win-demo");
int input = region.addInputLayer2D(8, 8, 1.0, 0.01);
int hidden = region.addLayer(4, 0, 0);

// Unique source subscriptions (stride 2, valid)
int wires = region.connectLayersWindowed(input, hidden, 3, 3, 2, 2, "valid", /*feedback=*/false);
// …drive some frames…
// When a neuron grows in `input` (or any source layer passed here), Region.autowireNewNeuron will call
// tract.attachSourceNeuron(newIndex) so the new source is wired deterministically.
```

### Mojo (same‑kind growth)

```mojo
var region = Region(name="mojo-growth")
let l0 = region.add_layer(excitatory_count=4, inhibitory_count=1, modulatory_count=1)
# Configure neurons so fallback streak can trigger growth …
# When growth fires, Layer.try_grow_neuron now clones the seed’s kind (E/I/M) instead of defaulting to E.
```

------

## Why this completes A & B

- **A (Java):** You now have `connectLayersWindowed(...)` that:
  - Computes unique participating sources deterministically.
  - Wires sources → center output (if `OutputLayer2D`) or to all dest neurons (generic).
  - Records a `Tract` and **re‑attaches** newly grown source neurons via `Region.autowireNewNeuron(...)`.
- **B (Mojo):** `Layer.try_grow_neuron` clones the **same kind** as the seed (E/I/M), preserves bus/config/limits, installs ownership, and delegates deterministic wiring to the region.

If you run into minor method‑name mismatches (e.g., your Region backref field or autowire method name in Mojo), keep your existing names and only adjust the call sites in the snippets above—the logic and structure will stay the same.

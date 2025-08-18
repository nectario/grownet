Love it—let’s instrument **one tick end‑to‑end** and watch it hop **neuron → layer → region** in both **Java** (gold copy) and **Python** (mirror). Below is a practical, breakpoint‑first walkthrough plus tiny harnesses you can drop into your tree.

> **Note:** I don’t have your workspace open here, so I can’t cite exact line numbers. If you’d like me to point to precise files/lines, re‑upload the latest `src` because prior uploads in this chat expire over time.

------

## A. Where to put breakpoints (map once, use everywhere)

These locations give you a clean “spine” of the signal path. Names follow the contract and your current code base conventions.

| Stage                        | Java (gold) – suggested breakpoint method                    | Python (mirror) – suggested breakpoint method                | Why this matters                                             |
| ---------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Ingest input                 | `Region.tick(String port, double value)`                     | `Region._tick(port: str, value: float)`                      | Start of a tick; set a logpoint to print the port/value.     |
| Resolve input bindings       | `Region.bindInput(...)` is done beforehand; in `tick` step into the code that iterates bound input layers | `Region._tick` where it fetches `_input_bindings[port]`      | Confirms which **layers** are driven by this port.           |
| Layer fan‑in → neurons       | `Layer.propagateFrom(int sourceIndex, double value)` (or the layer’s intake path) | `Layer._propagate_from(source_index: int, value: float)`     | First place value hits a layer. For `InputLayer2D`/`OutputLayer2D`, use those overrides. |
| Neuron receives input        | `Neuron.onInput(double value)`                               | `Neuron._on_input(value: float)`                             | See thresholding/accumulation prior to firing.               |
| Slot selection & learning    | `SlotEngine.selectOrCreateSlot(Neuron who, double value)` (or equivalent) + `Weight.reinforce(...)` | `SlotEngine._select_or_create_slot(who: Neuron, value: float)` + `Weight._reinforce(...)` | Watch slot/weight chosen and reinforcement.                  |
| Neuron fires                 | `Neuron.fire(double outputValue)` (and subclasses) **and** `Neuron.registerFireHook(...)` callback | `Neuron._fire(output_value: float)` and `_register_fire_hook(...)` | The moment a neuron emits and the **fire hook** runs.        |
| Across a tract (layer→layer) | `Tract.onSourceFired(Neuron who, double value)` and `Synapse.transmit(...)` | `Tract._on_source_fired(who: Neuron, value: float)` and `Synapse._transmit(...)` | Fan‑out over synapses to the destination layer(s).           |
| Destination neuron intake    | `Neuron.onInput(...)` (on the **destination** neuron)        | `Neuron._on_input(...)`                                      | Confirms the value that arrives after weight.                |
| Output binding               | Code in `Region.tick(...)` that collects/updates outputs     | `Region._tick(...)` where `_output_bindings` are consulted   | Observe what leaves the region (if applicable).              |
| Metrics & book‑keeping       | `RegionMetrics` construction (inside `tick`)                 | `_RegionMetrics` (or dict) just before return                | Sanity check on counts you expect for this path.             |

**Tip (IntelliJ IDEA/CLion):** enable *Step filters* (Preferences → Build, Execution, Deployment → Debugger → Stepping → Step Filters) to skip JDK collections; use **Force Step Into** (Alt+Shift+F7) to step into lambdas (e.g., your fire‑hook).

**Tip (VS Code/PyCharm):** prefer **logpoints**/**conditional breakpoints** to avoid stopping on every neuron. Example conditions you’ll use a lot:

- Java: `who.getName().equals("E0")` or `this.getName().equals("Layer0")`
- Python: `who._name == "E0"` or `self._name == "Layer0"`

------

## B. Minimal **Java** harness for single‑tick tracing

Create `src/java/demo/DebugSingleTick.java` (package/folder as you prefer). This mirrors your API and uses the `FireHook` you already have.

```java
// package demo;

import grownet.Region;
import grownet.Layer;
import grownet.Tract;
import grownet.Neuron;
import grownet.FireHook;
import grownet.RegionMetrics;

import java.util.List;

public class DebugSingleTick {
    public static void main(String[] args) {
        // --- 1) Region & layers ------------------------------------------------
        Region region = new Region("dbg");
        int L0 = region.addLayer(1, 0, 0); // 1 excitatory neuron
        int L1 = region.addLayer(1, 0, 0); // another layer to watch fan-out

        // --- 2) Wiring ---------------------------------------------------------
        region.bindInput("in", List.of(L0));
        region.bindOutput("out", List.of(L1));
        Tract t01 = region.connectLayers(L0, L1, /*prob*/1.0, /*feedback*/false);

        // --- 3) Fire hook (log without pausing); set a breakpoint inside this --
        FireHook hook = (Neuron who, double value) ->
            System.out.printf("FIRE %s  value=%.4f  layer=%s%n",
                    who.getName(), value, who.getLayer().getName());

        // Register hook on all neurons in both layers
        for (Neuron n : region.getLayers().get(L0).getNeurons()) n.registerFireHook(hook);
        for (Neuron n : region.getLayers().get(L1).getNeurons()) n.registerFireHook(hook);

        // --- 4) BREAKPOINTS YOU WANT ------------------------------------------
        // Set breakpoints here:
        // - Region.tick(...)
        // - Layer.propagateFrom(...)
        // - Neuron.onInput(...)
        // - SlotEngine.selectOrCreateSlot(...)
        // - Neuron.fire(...)
        // - Tract.onSourceFired(...)
        // - Synapse.transmit(...)
        // - return of Region.tick (inspect RegionMetrics)

        // --- 5) Drive one tick -------------------------------------------------
        RegionMetrics m = region.tick("in", 1.0);

        System.out.printf("Metrics: deliveredEvents=%d, totalSlots=%d, totalSynapses=%d%n",
                m.getDeliveredEvents(), m.getTotalSlots(), m.getTotalSynapses());
    }
}
```

**What to watch as you step:**

1. **`Region.tick`** – confirm the input port `"in"` maps to `L0`.
2. **`Layer.propagateFrom` (L0)** – see the value that goes into the first neuron.
3. **`Neuron.onInput` (E0 in L0)** – observe any accumulation/thresholding.
4. **`SlotEngine.selectOrCreateSlot` → `Weight.reinforce`** – which slot & strength.
5. **`Neuron.fire` (E0)** – your **hook** prints; breakpoint here is very illustrative.
6. **`Tract.onSourceFired`/`Synapse.transmit`** – value * weight reaches `L1`.
7. **`Neuron.onInput` (dest E0 in L1)** – confirm post‑weight value.
8. **`Region.tick` return** – inspect `RegionMetrics`.

> **Optional:** to see **layer→layer→layer**, add `int L2 = region.addLayer(1,0,0)` and chain another `connectLayers(L1, L2, 1.0, false)`; register hooks for L2 as well.

------

## C. Minimal **Python** harness for single‑tick tracing

Mirror of the Java path using the underscore API you requested. Save as `python/debug_single_tick.py`.

```python
# from region import Region  # adapt imports to your layout
# from neuron import Neuron  # if you expose types
# Exact module names may differ in your project; adjust accordingly.

def _log_fire(who, value: float):
    # Set a breakpoint here, or keep as a "tracepoint" style print
    print(f"FIRE {who.name}  value={value:.4f}  layer={who._layer.name}")


def main():
    region = Region("dbg")
    L0 = region._add_layer(1, 0, 0)
    L1 = region._add_layer(1, 0, 0)

    region._bind_input("in", [L0])
    region._bind_output("out", [L1])
    region._connect_layers(L0, L1, 1.0, False)

    # Register hooks (adjust to your API; many projects expose layer._neurons)
    for n in region.layers[L0]._neurons:
        n._register_fire_hook(_log_fire)
    for n in region.layers[L1]._neurons:
        n._register_fire_hook(_log_fire)

    # Breakpoints to set:
    # - Region._tick
    # - Layer._propagate_from
    # - Neuron._on_input
    # - SlotEngine._select_or_create_slot
    # - Neuron._fire
    # - Tract._on_source_fired, Synapse._transmit
    # - end of Region._tick (metrics)

    metrics = region._tick("in", 1.0)
    print("Metrics:", metrics)


if __name__ == "__main__":
    main()
```

**Debugging tips (Python):**

- In VS Code, use a **logpoint** on `Neuron._fire` with message:

  ```
  FIRE {who._name} value={value} layer={who._layer._name}
  ```

- If you prefer console stepping, insert `breakpoint()` in `Region._tick` and `Neuron._fire`.

------

## D. Nice‑to‑have debug polish (both languages)

1. **Conditional breakpoints**
    Break only when a specific neuron/layer fires:
   - Java condition: `who.getName().equals("E0")`
   - Python condition: `who._name == "E0"`
2. **Trace across just one tract**
    Set a condition in `Tract.onSourceFired`/`_on_source_fired`:
   - Java: `this.getId() == 0` (or compare `getSrc().getName()` / `getDst().getName()`)
   - Python: `self._src._name == "Layer0" and self._dst._name == "Layer1"`
3. **Watch expressions**
    Add these to the debugger:
   - **Pre‑fire:** `this.name` / `self._name`, `value`, `slot.id` / `slot._id`, `weight.strength`.
   - **Synapse:** `syn.getWeight().getStrength()` / `syn._weight._strength`.
   - **Metrics:** `m.getDeliveredEvents()` or `metrics["delivered_events"]`.
4. **Don’t pause on every hook**
    Make the fire‑hook a **logpoint** (Java: “Evaluate and log”) so the program keeps flowing while printing the route.
5. **Step into lambdas**
    In Java, use **Force Step Into** to enter your `FireHook` lambda.

------

## E. (Optional) Region→Region trace

Regions are usually independent containers. To simulate **region→region** flow in one debug run:

- Make **Region A** with output port `"outA"` bound to its last layer(s).
- After `A.tick("inA", value)` returns, read your output (e.g., the average `OutputNeuron` emission or a dedicated getter), then **feed that into Region B**: `B.tick("inB", out_value)`.
- Place the same breakpoints in B to watch the “handoff”.

(If you later add a `RegionLink` or multi‑region bus, you can break at its `transmit` function in exactly the same way you do for `Tract`.)

------

## F. What a clean single‑tick trace should look like

A typical console trace (from your hooks/logpoints) for the two‑layer harness:

```
Region.tick: port=in, value=1.0000
Layer L0 propagateFrom: value=1.0000
Neuron E0(L0) onInput: value=1.0000
SlotEngine.selectOrCreateSlot: slot=0, w=0.42  (example)
Neuron E0(L0) FIRE value=0.4200
Tract L0->L1 onSourceFired: who=E0, value=0.4200
Synapse transmit: weight=0.4200, delivered=0.4200
Neuron E0(L1) onInput: value=0.4200
Neuron E0(L1) FIRE value=0.1764    (if cascading with learning)
Region.tick: deliveredEvents=2, totalSlots=1, totalSynapses=1
```

If you don’t see the `Tract` or `Synapse` events:

- Ensure `connectLayers(L0, L1, 1.0, false)` was called.
- Check that `probability=1.0` (for deterministic wiring) and the graph was built before ticking.

------

## G. Common hiccups (and how to spot them quickly)

- **No fire in L0** → Put a breakpoint in `Neuron.onInput` and inspect threshold logic and the slot’s initial weight; drive a larger input (e.g., `2.0`) to force a first emission.
- **No delivery to L1** → Break in `Tract.onSourceFired` to confirm the `sourceIndex`/mapping is correct; verify `connectLayers` was invoked and *after* `addLayer`.
- **Hooks not printing** → In Java, ensure hooks are registered on the **actual** neuron instances in the region (not a copy). In Python, confirm `_register_fire_hook` stores your callback in the neuron and is called inside `_fire`.

------

If you want, I can also provide tiny **JUnit** (Java) and **pytest** (Python) tests that assert the exact hop sequence (E0@L0 → E0@L1) so you have a non‑interactive way to confirm the path on every change.

> **Reminder:** if you’d like me to annotate your **exact** files with “set a breakpoint here →” comments or tailor the harness imports to your package layout, please re‑upload the latest `src`/`python` folders (uploads expire), and I’ll wire them up precisely.
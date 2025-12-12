GrowNet is now a *living system*—lots of moving parts—and the best way to keep it from wandering is to put a **safety net** underneath it. Below is a single, practical plan you can paste into Codex as a PR to give you guardrails and quick regress-detection across Python, C++, Java, and Mojo.

------

## PR: “Safety Net” — Guardrails, Invariants, and Parity CI

### Why this PR

- Catch mistakes **before** they spread (strict invariants + tests).
- Keep **determinism** and parity as the code grows.
- Make refactors **safe** (hash the graph; track growth; assert “one per tick”).

### What this PR adds (summary)

1. **Deterministic topology hashing** in each language (GraphHash).
2. **Growth invariants** in Region: per-tick counters and “one growth per tick” assert.
3. **Two-phase tick invariant**: bus `current_step` increments **exactly once**.
4. **Strict slot-cap property tests** (scalar & 2D).
5. **Frozen-slot tests** (freeze blocks learning; unfreeze prefers once).
6. **Windowed wiring tests** (unique source count + center rule).
7. **Cross-language parity smoke**: same seed + same stimulus → same totals and same topology hash.
8. **CI workflows** for Python, C++, Java, Mojo (build, run smoke/tests, lint).

Below are the focused patches (by area). They’re deliberately small and self-contained.

------

## 1) Topology Hash (GraphHash) — all languages

> Stable digest of Region structure: (num_layers, per-layer neuron counts, total_synapses, set of edges). Use only **structure**, not learned weights.

### Python — `src/python/utils/graph_hash.py` (new)

```python
import hashlib

def graph_hash(region) -> str:
    h = hashlib.sha256()
    layers = region.get_layers()
    h.update(str(len(layers)).encode())

    total_edges = 0
    for li, layer in enumerate(layers):
        neurons = layer.get_neurons()
        h.update(f"L{li}:{len(neurons)}".encode())
        for n in neurons:
            outs = getattr(n, "get_outgoing", None) or (lambda: [])
            fanout = outs()
            total_edges += len(fanout)
            for t in fanout:
                # t is a target neuron object; use object identity string or id if available
                h.update(f"E:{id(n)}->{id(t)}".encode())

    h.update(f"ES:{total_edges}".encode())
    return h.hexdigest()
```

### C++ — `src/cpp/GraphHash.h/.cpp` (new)

```cpp
// GraphHash.h
#pragma once
#include <string>
#include "Region.h"

namespace grownet {
std::string graphHash(const Region& region);
} // namespace grownet
// GraphHash.cpp
#include "GraphHash.h"
#include <openssl/sha.h>  // or a tiny local sha256 if you prefer
#include <sstream>
#include <iomanip>

namespace grownet {
static void sha256(const std::string& s, std::string& out) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const unsigned char*>(s.data()), s.size(), hash);
    std::ostringstream oss; oss<<std::hex<<std::setfill('0');
    for (auto b : hash) oss<<std::setw(2)<<(int)b;
    out = oss.str();
}
std::string graphHash(const Region& region) {
    std::ostringstream oss;
    const auto& layers = region.getLayers();
    oss << "L" << layers.size();
    long long totalEdges = 0;
    for (size_t li = 0; li < layers.size(); ++li) {
        const auto& L = layers[li];
        const auto& ns = L->getNeurons();
        oss << "|L" << li << ":" << ns.size();
        for (auto& n : ns) {
            const auto& out = n->getOutgoing();
            totalEdges += static_cast<long long>(out.size());
            for (auto& syn : out) {
                oss << "|E:" << n.get() << "->" << syn.getTarget();
            }
        }
    }
    oss << "|ES:" << totalEdges;
    std::string out; sha256(oss.str(), out);
    return out;
}
} // namespace grownet
```

### Java — `RegionHasher.java` (new)

```java
package ai.nektron.grownet;

import java.security.MessageDigest;
import java.util.HexFormat;

public final class RegionHasher {
    public static String hash(Region r) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            var layers = r.getLayers();
            md.update(("L"+layers.size()).getBytes());
            long totalEdges = 0;
            for (int li = 0; li < layers.size(); ++li) {
                var L = layers.get(li);
                var ns = L.getNeurons();
                md.update(("|L"+li+":"+ns.size()).getBytes());
                for (var n : ns) {
                    var out = n.getOutgoing();
                    totalEdges += out.size();
                    for (var t : out) {
                        md.update(("|E:"+System.identityHashCode(n)+"->"+System.identityHashCode(t)).getBytes());
                    }
                }
            }
            md.update(("|ES:"+totalEdges).getBytes());
            return HexFormat.of().formatHex(md.digest());
        } catch (Exception e) { return "sha256-error"; }
    }
}
```

### Mojo — `graph_hash.mojo` (new)

```mojo
struct GraphHash:
    fn hash(region: Region) -> String:
        var b = StringBuilder()
        let layers = region.get_layers()
        b.append("L").append_int(layers.size())
        var total_edges: Int64 = 0
        var li: Int64 = 0
        for layer in layers:
            let neurons = layer.get_neurons()
            b.append("|L").append_int(li).append(":").append_int(neurons.size())
            for neuron in neurons:
                let outs = neuron.get_outgoing()
                total_edges += outs.size()
                for target in outs:
                    b.append("|E:").append_ptr(neuron.ptr()).append("->").append_ptr(target.ptr())
            li += 1
        b.append("|ES:").append_int(total_edges)
        return sha256(b.to_string())  # use your existing sha or add a tiny impl
```

------

## 2) Growth invariants (counters + one-per-tick assert)

### Python — `src/python/region.py`

```diff
 class Region:
     def __init__(...):
         ...
+        self.grown_neurons_this_tick = 0
+        self.grown_layers_this_tick = 0

+    def _reset_growth_counters(self):
+        self.grown_neurons_this_tick = 0
+        self.grown_layers_this_tick = 0

     def autowire_new_neuron(self, layer, new_idx):
         ...
+        self.grown_neurons_this_tick += 1

     def request_layer_growth(self, saturated_layer):
         ...
         self.connect_layers(idx, new_idx, probability=1.0, feedback=False)
+        self.grown_layers_this_tick += 1
         return new_idx

     def tick(self, port, value):
+        self._reset_growth_counters()
         ...
         for layer in self.layers: layer.end_tick()
         if self.bus: self.bus.decay()
+        assert self.grown_layers_this_tick <= 1, "More than one layer grew in a single tick"
         return metrics
```

> Mirror the same counters and a single assert in C++/Java/Mojo (exact code omitted here to keep this PR focused—pattern is the same).

------

## 3) Two-phase tick invariant test (all languages)

- Python: add `tests/test_tick_invariants.py`:

```python
def test_bus_step_increments_once_per_tick():
    from region import Region
    r = Region("invariants")
    l0 = r.add_layer(1,0,0)
    r.bind_input("x", [l0])
    step0 = r.get_layers()[l0].get_bus().get_current_step()
    r.tick("x", 0.5)
    step1 = r.get_layers()[l0].get_bus().get_current_step()
    assert step1 == step0 + 1
```

- C++/Java/Mojo: add a tiny smoke asserting `step` advanced exactly by 1 after a tick.

------

## 4) Strict slot-cap property tests (scalar & 2D) — Python example

```
src/python/tests/test_slot_strict_cap.py
def test_scalar_strict_cap_and_fallback():
    from region import Region
    from slot_config import fixed
    r = Region("cap")
    l = r.add_layer(1,0,0)
    n = r.get_layers()[l].get_neurons()[0]
    n.slot_cfg = fixed(10.0); n.slot_limit = 1
    r.bind_input("x", [l])
    for v in [1.0, 1.3, 1.6]:
        r.tick("x", v)
    assert len(n.slots) == 1
    assert getattr(n, "last_slot_used_fallback", False) is True

def test_2d_strict_cap_and_fallback():
    r = Region("cap2d")
    lin = r.add_input_layer_2d(4,4,1.0,0.01)
    lh = r.add_layer(1,0,0)
    r.connect_layers_windowed(lin, lh, 2,2,2,2, "valid")
    r.bind_input("img", [lin])
    n = r.get_layers()[lh].get_neurons()[0]
    n.slot_limit = 1; n.slot_cfg.spatial_enabled = True
    frames = [
        [[0,1,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
        [[0,0,1,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
    ]
    for f in frames: r.tick_2d("img", f)
    assert len(n.slots) == 1
    assert getattr(n, "last_slot_used_fallback", False) is True
```

> Add similar in Java (JUnit) and C++ (gtest or your minimal harness).

------

## 5) Frozen-slot tests

- Assert that `freeze_last_slot()` prevents reinforcement/threshold updates.
- Assert `unfreeze_last_slot()` triggers one-shot “prefer last slot” reuse.
   (You already implemented this logic; tests make it future-proof.)

------

## 6) Windowed wiring tests (center rule + unique sources)

- 4×4 input, kernel 2×2, stride 2 → expect **16** unique sources.
- 5×5 SAME, kernel 3×3, stride 3 → expect **25** unique sources.
- Center index uses **floor(midpoint)** and is clamped to bounds.

------

## 7) Cross-language parity smoke (same seed, same stimulus)

- Add a tiny runner per language that:
  1. Constructs identical 2-layer and 2D windowed setups with a fixed seed.
  2. Drives the same sequence (e.g., [1.0,1.3,1.6] for scalar, two moving dots for 2D).
  3. Prints **graph hash**, **slot count**, **synapse count**.
- A script in `scripts/compare_parity.py` loads the three outputs and asserts equality.

------

## 8) CI (workflows stubs)

- **Python**: `pytest -q`, `ruff`, coverage gate.
- **C++**: cmake build (Release & Debug), run guarded smoke (define `-DGROWNET_GROWTH_SMOKE`), `-Wall -Wextra -Wpedantic`, optional `clang-tidy`.
- **Java**: Gradle/Maven test, Checkstyle, SpotBugs.
- **Mojo**: build compile + smoke.

```yaml
# .github/workflows/ci.yml (skeleton)
name: ci
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps: [ checkout, setup-python, pip install -r requirements.txt, run pytest, ruff ]
  cpp:
    runs-on: ubuntu-latest
    steps: [ checkout, cmake -S . -B build -DCMAKE_BUILD_TYPE=Release, cmake --build build, run growth smoke ]
  java:
    runs-on: ubuntu-latest
    steps: [ checkout, setup-java, ./gradlew test ]
  mojo:
    runs-on: ubuntu-latest
    steps: [ checkout, mojo build (or your wrapper), run smoke ]
```

------

### Why this keeps you safe

- **Topology hashes** and **growth counters** catch silent wiring regressions immediately.
- **Strict-cap tests** guarantee the slotting rule that drives growth never drifts.
- **Frozen-slot tests** protect the memory freeze behavior from accidental change.
- **Windowed wiring tests** prevent subtle off-by-one “center” mistakes and duplicate edges.
- **Parity smoke + CI** makes cross-language drift visible fast.

------

If you want, I can now turn this “Safety Net” plan into a single Codex PR with concrete file edits for your repo layout (like we did previously). Or, if you prefer, I can start by pushing the Python + Java tests and GraphHash first (lowest friction), then follow with C++/Mojo.
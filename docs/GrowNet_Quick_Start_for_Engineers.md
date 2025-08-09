# GrowNet — Quick Start for Engineers

This is a practical, language‑by‑language “how to run it” guide for **GrowNet’s unified onInput/onOutput** architecture. It complements the broader design spec you already have. fileciteturn6file0

---

## 0) Mental model (60 seconds)

- **Every neuron** implements **two methods**:
  - `onInput(value, …) -> fired: bool` — gate + local learning; returns whether the neuron spiked.
  - `onOutput(amplitude)` — called **only if** it fired; sinks (outputs) *accumulate*, others typically no‑op.
- **Two‑phase tick** in `Region`:
  - **Phase A:** inject input → layers do `onInput` → (if fired) `onOutput` → local propagation.
  - **Phase B:** inter‑layer tracts flush **once**. Then output layers do `end_tick()` to finalize frames.
- **Buses**: each layer has a `LateralBus` carrying **inhibition** and **modulation**, both decaying to neutral.
- **Slots (weights)**: per‑neuron thresholds adapt via **T0 imprint + T2 homeostasis**.

ASCII view:
```
Input → [InputLayer2D] → [Hidden E/I/M] → [OutputLayer2D] → Frame
          |  bus            |  bus             |  bus
          +------ Phase A (local) ------+  Phase B (tract flush)
```

---

## 1) Recommended defaults

```text
beta = 0.01           # EMA horizon for spike-rate estimate
eta = 0.02            # threshold adaptation speed
r_star = 0.05         # target spike rate per slot
epsilon_fire = 0.01   # initial slack for T0 imprint
t0_slack = 0.02       # same-stimulus re-fire margin
slot_hit_saturation = 10000
```

---

## 2) Python (reference)

**Minimal image pipeline (28×28):**
```python
import numpy as np
from region import Region

imageHeight, imageWidth = 28, 28
region = Region("image_io")

idxInput  = region.add_input_layer_2d(imageHeight, imageWidth, gain=1.0, epsilon_fire=0.01)
idxHidden = region.add_layer(excitatory_count=64, inhibitory_count=8, modulatory_count=4)
idxOutput = region.add_output_layer_2d(imageHeight, imageWidth, smoothing=0.2)

region.bind_input("pixels", [idxInput])
region.connect_layers(idxInput, idxHidden, probability=0.05, feedback=False)
region.connect_layers(idxHidden, idxOutput, probability=0.12, feedback=False)

for step in range(20):
    frameIn = np.zeros((imageHeight, imageWidth), dtype=float)
    frameIn[(step * 2) % imageHeight, step % imageWidth] = 1.0  # moving dot

    metrics = region.tick_image("pixels", frameIn)  # Phase A + B + finalize
    if (step + 1) % 5 == 0:
        outLayer = region.layers[idxOutput]           # OutputLayer2D
        imageOut = outLayer.get_frame()
        print(f"{step+1:02d}: delivered={int(metrics['delivered_events'])} "
              f"mean={imageOut.mean():.4f} nonzero={(imageOut>0.05).sum()}")
```

**Notes**
- Output neurons **never** propagate; their `onOutput` just accumulates and `end_tick()` smooths to the frame.
- If your `InputNeuron.onInput` already calls `self.fire(...)`, keep it (simple) or remove it and let `Layer` handle routing—either works as long as it’s consistent project‑wide.

---

## 3) Java (Maven / IntelliJ)

**Main class:**
```java
package ai.nektron.grownet;

import java.util.Map;

public class ImageIODemo {
    public static void main(String[] args) {
        int h = 28, w = 28;
        Region region = new Region("image_io");

        int lIn     = region.addInputLayer2D(h, w, 1.0, 0.01);
        int lHidden = region.addLayer(64, 8, 4);
        int lOut    = region.addOutputLayer2D(h, w, 0.2);

        region.bindInput("pixels", java.util.List.of(lIn));
        region.connectLayers(lIn, lHidden, 0.05, false);
        region.connectLayers(lHidden, lOut, 0.12, false);

        for (int step = 0; step < 20; step++) {
            double[][] frame = new double[h][w];
            frame[(step * 2) % h][step % w] = 1.0; // moving dot

            Map<String, Double> m = region.tickImage("pixels", frame);
            if ((step + 1) % 5 == 0) {
                OutputLayer2D out = (OutputLayer2D) region.getLayers().get(lOut);
                double[][] img = out.getFrame();
                double sum = 0.0; int nz = 0;
                for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
                    sum += img[y][x]; if (img[y][x] > 0.05) nz++;
                }
                System.out.printf("[%d] delivered=%d mean=%.4f nonzero=%d%n",
                    step + 1, m.get("delivered_events").intValue(), sum/(h*w), nz);
            }
        }
    }
}
```

**Make sure your Region exposes**: `addInputLayer2D`, `addOutputLayer2D`, `tickImage`, and `getLayers()` (for reading the frame). Your `Layer` should call `neuron.onOutput(value)` when `fired` is true.

---

## 4) C++ (CLion / CMake)

**CMake snippet:**
```cmake
add_executable(image_io_demo
    src/cpp/ImageIODemo.cpp
    # plus your sources for Region/Layer/Neuron/Weight...
)
target_include_directories(image_io_demo PRIVATE src/cpp)
```

**Demo main:**
```cpp
#include <iostream>
#include <vector>
#include <memory>
#include "Region.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

int main() {
    const int h = 28, w = 28;
    grownet::Region region("image_io");

    int lIn     = region.addInputLayer2D(h, w, 1.0, 0.01);
    int lHidden = region.addLayer(64, 8, 4);
    int lOut    = region.addOutputLayer2D(h, w, 0.2);

    region.bindInput("pixels", { lIn });
    region.connectLayers(lIn, lHidden, 0.05, false);
    region.connectLayers(lHidden, lOut, 0.12, false);

    for (int step = 0; step < 20; ++step) {
        std::vector<std::vector<double>> frame(h, std::vector<double>(w, 0.0));
        frame[(step * 2) % h][step % w] = 1.0;

        auto m = region.tickImage("pixels", frame);
        if ((step + 1) % 5 == 0) {
            auto out = std::dynamic_pointer_cast<grownet::OutputLayer2D>(region.getLayers()[lOut]);
            const auto& img = out->getFrame();
            double sum = 0.0; int nz = 0;
            for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) {
                sum += img[y][x]; if (img[y][x] > 0.05) nz++;
            }
            std::cout << "[" << (step + 1) << "] delivered=" << m.delivered_events
                      << " mean=" << (sum / (h * w)) << " nonzero=" << nz << std::endl;
        }
    }
}
```

**Ensure**: `Neuron` has `virtual void onOutput(double) {}` and `Layer` calls it when `fired` is true. Output layer calls `endTick()` each tick to finalize the frame.

---

## 5) Mojo

**Run:**
```bash
mojo run mojo/image_io_demo.mojo
```

**Demo (moving dot):**
```mojo
from region import Region

fn generate_frame(h: Int64, w: Int64, step: Int64) -> Array[Array[Float64]]:
    var img = Array[Array[Float64]](h)
    for y in range(h):
        var row = Array[Float64](w)
        for x in range(w): row[x] = 0.0
        img[y] = row
    img[Int((step*2) % h)][Int(step % w)] = 1.0
    return img

fn main():
    let h: Int64 = 28; let w: Int64 = 28
    var region = Region("image_io")
    let inIdx = region.add_input_layer_2d(h, w, 1.0, 0.01)
    let hidIdx = region.add_layer(64, 8, 4)
    let outIdx = region.add_output_layer_2d(h, w, 0.2)
    region.bind_input("pixels", [inIdx])
    region.connect_layers(inIdx, hidIdx, 0.05, False)
    region.connect_layers(hidIdx, outIdx, 0.12, False)

    for step in range(20):
        let frame = generate_frame(h, w, step)
        let m = region.tick_image("pixels", frame)
        if ((step + 1) % 5) == 0:
            print("step=", step+1, " delivered=", m["delivered_events"])
```

**Ensure** your `Layer` calls `neuron.onOutput(value)` when `fired`. In `Region.tick_image`, call `end_tick()` on `OutputLayer2D` before bus decay.

---

## 6) API cheat sheet

| Area   | Call | Notes |
|---|---|---|
| Region | `add_input_layer_2d(h, w, gain, epsilon_fire)` / `addInputLayer2D` | Creates shape‑aware sensor layer |
|       | `add_layer(excitatory_count, inhibitory_count, modulatory_count)` | Hidden mixed‑type layer |
|       | `add_output_layer_2d(h, w, smoothing)` / `addOutputLayer2D` | Shape‑aware output buffer |
|       | `bind_input(port, [layerIndexes])` / `bindInput` | Map a named input to 1+ entry layers |
|       | `connect_layers(src, dst, probability, feedback)` | Wire inter‑layer tracts |
|       | `tick_image(port, image)` / `tickImage` | Run Phase A + B + finalize; returns metrics |
| Layer  | `forward(value)` (scalar) / `forward_image(image)` | Inject into a layer (Phase A) |
| Neuron | `onInput(value, …) -> bool` | Gate + learn locally |
|       | `onOutput(amplitude)` | Called only if fired; outputs accumulate |

---

## 7) Troubleshooting

- **Frame stays all zeros** → check that your output layer’s `end_tick()/endTick()` is called in the `Region` tick; ensure thresholds aren’t too high (lower `eta` or raise `r_star` slightly).
- **Too many firings (chatter)** → raise `r_star` or `beta` a bit; increase `epsilon_fire`; add mild inhibition (e.g., inhibitory bus factor 0.8 for 1–2 ticks).
- **No growth** when you expect new slots → verify your slot creation trigger (e.g., %‑delta bucketing or distance threshold) is enabled.
- **Compilation error: `onOutput` undefined** → add the no‑op method to the base `Neuron` and make sure `Layer` calls it only when `fired` is true.
- **Double routing** → if `InputNeuron.onInput` calls `fire(...)` and your `Layer` also routes on `fired`, pick one (project‑wide) to avoid duplicates.

---

## 8) Next steps

- Run the demos in each language and compare metrics.
- Toggle **pruning** and watch delivered events and nonzero frame counts over time.
- Turn on **slot growth** and log each allocation: slot id, θ, strength, hit_count.

If you want, I can also generate a one‑page printable cheat sheet (A4/Letter) with just the API & defaults.
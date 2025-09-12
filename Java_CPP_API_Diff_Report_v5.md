# Java ↔ C++ Public API Parity — v5 Contract Alignment (Report + Checklist)

> **Status of this file**  
> This report was generated in-chat without opening your latest source ZIP (file access to uploaded ZIPs is not available here).  
> It contains a **contract-aligned checklist**, a **diff template**, and **patch suggestions** derived from the v5 design/contract and from build logs you shared.  
> If you want a *source-accurate* diff, run the commands in the “How to auto‑diff API surfaces locally” section and paste results back — I’ll translate them into exact patch hunks.

---

## Executive summary

Our goal is to make **Java** and **C++** expose the **same public surface** for core types defined by the v5 contract:
**Region, Layer, Neuron, SlotConfig, GrowthPolicy, RegionBus, Tract, TractWindowed, RegionMetrics, ProximityConfig/Engine**.

A few typical drifts (seen in logs or common pitfalls) to normalize:
- **Method naming & overloads** — e.g., `bindInput2D` shape overload, windowed wiring return value and padding token (“SAME”/“VALID”).
- **Metrics names** — C++ uses `camelCase` fields (e.g., `totalSlots`); demos/tests sometimes referenced `snake_case` (e.g., `total_slots`). Align on **camelCase** fields in C++ and **getters** in Java: `getTotalSlots()`, `getTotalSynapses()`.
- **Policy wiring** — ensure `setProximityConfig(ProximityConfig)` exists in both languages and is invoked once per tick **after Phase‑B** and before `bus.decay()`.
- **SlotConfig fluent setters** — C++ has `setSlotLimit(int)`, `setMinDeltaPctForGrowth(double)`, etc. Ensure Java mirrors these names exactly.

---

## Contract‑aligned public API shape (authoritative intent)

Below are the **intended** public signatures. Use them as the source of truth when normalizing Java/C++.

### Region

```text
// Construction
Region(string name)

// Add layers
int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount)
int addInputLayer2D(int height, int width, double gain, double epsilonFire)
int addOutputLayer2D(int height, int width, double smoothing)
int addInputLayerND(int[] shape, double gain, double epsilonFire)          // C++: vector<int>, Java: int[]

// Binding
void bindInput(String port, int[] attachLayers)                            // C++: vector<int>
void bindInput2D(String port, int height, int width, double gain, double epsilonFire, int[] attachLayers)
void bindInput2D(String port, int[] shape, double gain, double epsilonFire, int[] attachLayers)  // shape overload
void bindInputND(String port, int[] shape, double gain, double epsilonFire, int[] attachLayers)
void bindOutput(String port, int[] attachLayers)

// Connectivity
Tract& connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback)
int connectLayersWindowed(int sourceIndex, int destIndex,
                          int kernelH, int kernelW, int strideH, int strideW,
                          String padding /* "SAME" | "VALID" */, boolean feedback)

// Ticks
RegionMetrics tick(String port, double value)
RegionMetrics tick2D(String port, double[][] frame)            // C++: vector<vector<double>>
RegionMetrics tickND(String port, double[] flat, int[] shape)  // C++: vector<double>, vector<int>

// Pulses
void pulseInhibition(double factor)
void pulseModulation(double factor)

// Growth hooks
void setGrowthPolicy(GrowthPolicy policy)                      // value or reference semantics per language
void maybeGrowRegion()

// Optional proximity policy
void setProximityConfig(ProximityConfig config)
```

### RegionMetrics (fields in C++; getters in Java)

```text
// Required counters
long deliveredEvents
long totalSlots
long totalSynapses

// Optional spatial metrics
long   activePixels
double centroidRow, centroidCol
int    bboxRowMin, bboxRowMax, bboxColMin, bboxColMax
```

### SlotConfig (selected)

```text
// Growth gates
bool   growthEnabled
bool   neuronGrowthEnabled
int    slotLimit
bool   fallbackGrowthRequiresSameMissingSlot
double minDeltaPctForGrowth     // e.g., 70.0 to gate growth to large deltas

// Fluent setters (mirror names exactly)
SlotConfig& setGrowthEnabled(bool)
SlotConfig& setNeuronGrowthEnabled(bool)
SlotConfig& setSlotLimit(int)
SlotConfig& setFallbackGrowthRequiresSameMissingSlot(bool)
SlotConfig& setMinDeltaPctForGrowth(double)
```

### GrowthPolicy (selected)

```text
bool   enableRegionGrowth
int    layerCooldownTicks
int    maximumLayers
double connectionProbability
double averageSlotsThreshold
double percentAtCapFallbackThreshold  // 0.0 disables the OR‑trigger branch
```

### ProximityConfig + ProximityEngine (selected)

```text
bool   proximityConnectEnabled
double proximityRadius
enum   proximityFunction { STEP, LINEAR, LOGISTIC }
double linearExponentGamma
double logisticSteepnessK
int    proximityMaxEdgesPerTick
int    proximityCooldownTicks
long   developmentWindowStart, developmentWindowEnd
bool   recordMeshRulesOnCrossLayer
```

And a single integration call per tick (after Phase‑B, before `bus.decay()`):
```text
if (proximity.enabled) ProximityEngine.apply(region, proximityConfig);
```

---

## Typical Java ↔ C++ drifts to normalize (actionable checklist)

1) **`bindInput2D` shape overload**  
   - **C++** *present*: `void bindInput2D(std::string, std::vector<int> shape, double gain, double eps, std::vector<int>)` (forwards to H×W).  
   - **Action (Java)**: ensure **both** overloads exist:
     - `bindInput2D(String, int height, int width, double gain, double epsilonFire, List<Integer> layers)`
     - `bindInput2D(String, int[] shape, double gain, double epsilonFire, List<Integer> layers)`

2) **`connectLayersWindowed` result and padding**  
   - Return **`int` unique sources** in both languages.  
   - **Padding**: accept case‑insensitive `"SAME"`/`"VALID"` in both; normalize internally.

3) **`RegionMetrics` names**  
   - **C++**: fields `deliveredEvents`, `totalSlots`, `totalSynapses`, etc.  
   - **Java**: getters `getDeliveredEvents()`, `getTotalSlots()`, `getTotalSynapses()`, plus optional spatial getters.  
   - Update any demos/tests that still reference `snake_case` (`total_slots`) to camelCase/getters.

4) **`SlotConfig` fluent setters**  
   - Ensure **both** sides expose the exact setter names listed above.  
   - Confirm `setSlotLimit(int)` exists (C++ added; Java must match).

5) **Proximity policy plumbing**  
   - Ensure `setProximityConfig(ProximityConfig)` exists in **Region** in both languages.  
   - Ensure the **tick** path calls `ProximityEngine.apply(...)` at the right spot (after propagation/growth, before decay).

6) **Windowed wiring parity**  
   - `connectLayersWindowed(...)` should create a **TractWindowed** (not ad‑hoc edges) so that **auto‑reattach on growth** works in both languages.

---

## Minimal PR patch list (language‑specific)

> Use this as the blueprint for your Codex CLI run. When you paste this to Codex, reference file paths in your repo.

### C++

- **Region.h / Region.cpp**
  - Ensure:
    - `void setProximityConfig(const ProximityConfig&)`
    - `void bindInput2D(const std::string&, const std::vector<int>& shape, double, double, const std::vector<int>&)` (shape overload)
  - In `tick(...)`, `tick2D(...)`, `tickND(...)`: invoke proximity apply between Phase‑B and `bus.decay()`.

- **TractWindowed.h / TractWindowed.cpp**
  - Ensure accessor names are stable (`bool destinationIsOutput2D() const`), no trailing underscores in member names that leak into accessors.

- **SlotConfig.h**
  - Confirm fluent setters include `setSlotLimit(int)` and `setMinDeltaPctForGrowth(double)`.

- **RegionMetrics.h**
  - Keep `camelCase` fields (`totalSlots`, `totalSynapses`).

### Java

- **ai/nektron/grownet/Region.java**
  - Add `void setProximityConfig(ProximityConfig config)`.
  - Ensure overloads:
    - `bindInput2D(String port, int height, int width, double gain, double epsilonFire, List<Integer> attachLayers)`
    - `bindInput2D(String port, int[] shape, double gain, double epsilonFire, List<Integer> attachLayers)`
  - Ensure `connectLayersWindowed(...)` returns `int` unique sources and takes `String padding` (“SAME”/“VALID”).

- **ai/nektron/grownet/RegionMetrics.java**
  - Provide getters: `getDeliveredEvents()`, `getTotalSlots()`, `getTotalSynapses()`, plus spatial metrics getters.

- **ai/nektron/grownet/SlotConfig.java**
  - Add fluent setters mirroring C++ names exactly.

- **ai/nektron/grownet/policy/ProximityEngine.java**
  - Confirm the single tick integration site and config fields mirror C++ types/names.

---

## How to auto‑diff API surfaces locally (copy‑paste friendly)

1) **Java public API dump** (from your project root after `mvn -q -DskipTests package`):

```bash
# Adjust the classpath to your build output
JAR=target/grownet-*.jar
jar tf "$JAR" | sed -n 's#/#.#g;s#^.##p' | grep '^ai.nektron.grownet' > /tmp/j_classes.txt

# Dump signatures for key types
for C in ai.nektron.grownet.Region ai.nektron.grownet.RegionMetrics ai.nektron.grownet.SlotConfig ai.nektron.grownet.GrowthPolicy; do
  javap -classpath "$JAR" -public "$C" >> /tmp/j_api.txt
done
```

2) **C++ public API dump** (header scrape; adjust include path as needed):

```bash
# List public signatures (very lightweight regex extraction)
grep -nE '^(class|struct) (Region|RegionMetrics|SlotConfig|GrowthPolicy|Tract|TractWindowed)\b|^\s*(virtual\s+)?[A-Za-z_][A-Za-z0-9_:<>*&\s]*\([^;]*\)\s*;' -n src/cpp/*.h src/cpp/include/*.h > /tmp/cpp_api.txt
```

3) **Compare against the v5 contract (this checklist)**: open `/tmp/j_api.txt` and `/tmp/cpp_api.txt` side‑by‑side and check items in the checklists above. Paste both files back here and I’ll generate exact patch hunks for any divergences.

---

## Notes from your prior build logs (useful nudges)

- Demos referenced `RegionMetrics.total_slots`/`total_synapses`; C++ fields are `totalSlots`/`totalSynapses`. Update demos/tests to camelCase or Java getters.
- Added C++ overload `bindInput2D(String, int[] shape, ...)` — mirror this overload in Java.
- Fixed C++ `TractWindowed::destinationIsOutput2D()` accessor (name mismatch with member). Ensure Java accessor is consistent if exposed.
- CMake exclusions: avoid compiling tests/demos into the core library target; keep GoogleTest headers visible only to the test target.

---

### Ready‑to‑file parity task list

- [ ] Java: add `bindInput2D(String, int[] shape, ...)` overload; normalize padding tokens; return `int` unique sources.
- [ ] Java: add `setProximityConfig(ProximityConfig)` in `Region`; call engine in tick.
- [ ] Java: ensure `RegionMetrics` getters exist and names match C++ fields.
- [ ] C++: ensure `setProximityConfig(...)` exists and tick integration point is correct in all tick variants.
- [ ] C++: keep `TractWindowed` accessors consistent; ensure windowed wiring creates a tract for reattach parity.
- [ ] Both: mirror `SlotConfig` fluent setters (including `setSlotLimit`, `setMinDeltaPctForGrowth`).

---

**When you’re ready**, paste the Java `javap` dump and the C++ header scrape and I’ll turn this into a **precise, line‑level diff PR** across both languages.
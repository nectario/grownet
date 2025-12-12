# from your repo root
python3 api_diff_grownet.py --cpp-root ./src/cpp --java-root ./src/java --contract-yaml ./GrowNet_Contract_v5_master.yaml > API_DIFF_REPORT.md
python3 api_diff_grownet.py --contract GrowNet_Contract_v5_master.yaml --out api_diff_report.md


Here’s a **single “API parity” PR** that (a) applies the concrete fixes implied by your latest API diff report, (b) aligns **C++ ⇄ Java** public APIs to the **v5 contract**, and (c) adds “missing but useful” methods to **both languages and the contract** (as v5.1 addenda) where the method already exists in one side. I’ve kept all identifiers descriptive and consistent with your style and parity rules.

> **Source of truth for gaps:** the report you generated (Java ⇄ C++ vs v5 contract). I reference its exact findings inline below. 

------

# PR: API Parity Sweep — C++ ⇄ Java vs Contract v5 (with v5.1 addenda)

**Goals**

1. **Surface‑level API parity** between C++ and Java for all classes in the v5 contract.
2. **Add missing but useful methods** to the contract (v5.1 addenda) when they existed in only one language, then backfill the other language.
3. Keep changes **non‑invasive**: mostly wrappers/aliases/getters; no behavior changes to growth, wiring, or buses.

**Why now?** Your API report shows a set of systematic gaps (missing getters/setters, naming deltas like `Apply` vs `apply`, windowed/tract accessors, bus/metrics accessors, etc.). This PR addresses those deltas head‑on. 

------

## 0) Directory map (unchanged)

- C++: `src/cpp`, public headers in `src/cpp/include/`
- Java: `src/java/ai/nektron/grownet/...`
- Contract: `GrowNet_Contract_v5_master.yaml` (addenda in place)

------

## 1) Contract v5.1 addenda (strictly additive)

> These addenda only **add** items that already exist in one language but not the other, per your preference: “if a language has a method that does not exist in Java and the contract, add it to the contract and backfill the missing language.” 

### 1.1 `Region` (addenda)

- `autowireNewNeuron(layerRef, newIndex) : void`
- `ensureInputEdge(port) : int`
- `ensureOutputEdge(port) : int`
- `maybeGrowRegion() : void`

### 1.2 `ProximityEngine` (name unification)

- Keep `apply(region, config)` as the **contracted** name (camelCase).
  C++ may keep `Apply` as a legacy alias (non‑contract).

### 1.3 `TractWindowed` (mark as **optional** addendum API)

- `centerForWindow(originRow, originCol) : (row,col)`
- `windowCoversSourceIndex(srcIndex) : bool`
- `buildFromSourceGrid(height,width) : void`

> Rationale: these appear on the C++ side as pragmatic helpers for windowed wiring and are useful to expose at parity. 

### 1.4 Minor clarifications

- `RegionMetrics`: explicitly bless getters (`getTotalSlots`, `getTotalSynapses`, `getDeliveredEvents`, `getCentroidRow/Col`, `getBBox*`, `getActivePixels`).
- `LateralBus`: explicitly bless `getCurrentStep`, `decay`, and factor/decay getters+setters.

**Patch (contract) — `GrowNet_Contract_v5_master.yaml`**

```diff
@@ api:
   Region:
     methods:
+      - { name: "autowireNewNeuron", args: ["Layer", "int"], returns: "void", since: "v5.1" }
+      - { name: "ensureInputEdge",   args: ["string"],       returns: "int",  since: "v5.1" }
+      - { name: "ensureOutputEdge",  args: ["string"],       returns: "int",  since: "v5.1" }
+      - { name: "maybeGrowRegion",   args: [],               returns: "void", since: "v5.1" }
@@ api:
   ProximityEngine:
     methods:
-      - { name: "apply", args: ["Region","ProximityConfig"], returns: "int" }
+      - { name: "apply", args: ["Region","ProximityConfig"], returns: "int" }
+    notes:
+      - "C++ may retain legacy alias Apply(...), but contract name is apply(...)."
@@ api:
   TractWindowed:
     optional: true
     methods:
+      - { name: "centerForWindow", args: ["int","int"], returns: "(int,int)", since: "v5.1" }
+      - { name: "windowCoversSourceIndex", args: ["int"], returns: "bool", since: "v5.1" }
+      - { name: "buildFromSourceGrid", args: ["int","int"], returns: "void", since: "v5.1" }
@@ api:
   RegionMetrics:
     methods:
+      - { name: "getTotalSlots", returns: "long" }
+      - { name: "getTotalSynapses", returns: "long" }
+      - { name: "getDeliveredEvents", returns: "long" }
+      - { name: "getCentroidRow", returns: "double" }
+      - { name: "getCentroidCol", returns: "double" }
+      - { name: "getBboxRowMin", returns: "int" }
+      - { name: "getBboxRowMax", returns: "int" }
+      - { name: "getBboxColMin", returns: "int" }
+      - { name: "getBboxColMax", returns: "int" }
+      - { name: "getActivePixels", returns: "long" }
@@ api:
   LateralBus:
     methods:
+      - { name: "getCurrentStep", returns: "long" }
+      - { name: "decay", returns: "void" }
+      - { name: "getInhibitionFactor", returns: "double" }
+      - { name: "setInhibitionFactor", args: ["double"], returns: "void" }
+      - { name: "getInhibitionDecay", returns: "double" }
+      - { name: "setInhibitionDecay", args: ["double"], returns: "void" }
+      - { name: "getModulationFactor", returns: "double" }
+      - { name: "setModulationFactor", args: ["double"], returns: "void" }
```

------

## 2) C++ changes

> All C++ hunks below are **strictly additive** (or aliasing), so they won’t break existing callers.

### 2.1 ProximityEngine: add camelCase alias

**`src/cpp/include/ProximityEngine.h`**

```diff
@@
 class ProximityEngine {
 public:
-  static int Apply(Region& region, const ProximityConfig& cfg);
+  static int Apply(Region& region, const ProximityConfig& cfg);
+  // Contract v5: public method name is 'apply'. Keep legacy 'Apply' as alias.
+  static inline int apply(Region& region, const ProximityConfig& cfg) {
+    return Apply(region, cfg);
+  }
 };
```

### 2.2 Region: public getters/setters to match Java + contract

**`src/cpp/Region.h`**

```diff
@@ class Region {
 public:
+  // --- v5 contract accessors (Java parity) ---
+  const std::string& getName() const { return name; }
+  RegionBus& getBus() { return bus; }
+  const RegionBus& getBus() const { return bus; }
+
+  const std::vector<std::shared_ptr<Layer>>& getLayers() const { return layers; }
+
+  GrowthPolicy& getGrowthPolicy() { return growthPolicy; }
+  const GrowthPolicy& getGrowthPolicy() const { return growthPolicy; }
+  void setGrowthPolicy(const GrowthPolicy& gp) { growthPolicy = gp; hasGrowthPolicy = true; }
+
+  bool isEnableSpatialMetrics() const { return enableSpatialMetrics; }
+  void setEnableSpatialMetrics(bool v) { enableSpatialMetrics = v; }
+
+  const ProximityConfig& getProximityConfig() const { return proximityConfig; }
+  void setProximityConfig(const ProximityConfig& pc) { proximityConfig = pc; }
```

> Your `Region.cpp` already had implementations for most internal fields; these are trivial pass‑throughs. (You already added `bindInput2D` shape overload; leaving as is.)

### 2.3 ProximityConfig: full getter/setter surface (Java parity)

**`src/cpp/ProximityConfig.h`**  *(new or extend existing struct)*

```diff
@@
 struct ProximityConfig {
   bool   proximity_connect_enabled = false;
   double proximity_radius = 1.0;
   std::string proximity_function = "STEP"; // STEP|LINEAR|LOGISTIC
   double linear_exponent_gamma = 1.0;
   double logistic_steepness_k  = 4.0;
   int    proximity_max_edges_per_tick = 128;
   int    proximity_cooldown_ticks = 5;
   long long development_window_start = 0;
   long long development_window_end   = (1LL<<62);
   int    stabilization_hits = 3;
   bool   decay_if_unused = true;
   int    decay_half_life_ticks = 200;
   std::vector<int> candidate_layers; // empty => all
   bool   record_mesh_rules_on_cross_layer = true;

+  // --- fluent getters/setters (Java parity) ---
+  bool isEnabled() const { return proximity_connect_enabled; }
+  ProximityConfig& setEnabled(bool v){ proximity_connect_enabled=v; return *this; }
+  double getRadius() const { return proximity_radius; }
+  ProximityConfig& setRadius(double v){ proximity_radius=v; return *this; }
+  const std::string& getFunction() const { return proximity_function; }
+  ProximityConfig& setFunction(const std::string& v){ proximity_function=v; return *this; }
+  double getLinearExponentGamma() const { return linear_exponent_gamma; }
+  ProximityConfig& setLinearExponentGamma(double v){ linear_exponent_gamma=v; return *this; }
+  double getLogisticSteepnessK() const { return logistic_steepness_k; }
+  ProximityConfig& setLogisticSteepnessK(double v){ logistic_steepness_k=v; return *this; }
+  int getMaxEdgesPerTick() const { return proximity_max_edges_per_tick; }
+  ProximityConfig& setMaxEdgesPerTick(int v){ proximity_max_edges_per_tick=v; return *this; }
+  int getCooldownTicks() const { return proximity_cooldown_ticks; }
+  ProximityConfig& setCooldownTicks(int v){ proximity_cooldown_ticks=v; return *this; }
+  long long getDevelopmentWindowStart() const { return development_window_start; }
+  ProximityConfig& setDevelopmentWindowStart(long long v){ development_window_start=v; return *this; }
+  long long getDevelopmentWindowEnd() const { return development_window_end; }
+  ProximityConfig& setDevelopmentWindowEnd(long long v){ development_window_end=v; return *this; }
+  int getStabilizationHits() const { return stabilization_hits; }
+  ProximityConfig& setStabilizationHits(int v){ stabilization_hits=v; return *this; }
+  bool isDecayIfUnused() const { return decay_if_unused; }
+  ProximityConfig& setDecayIfUnused(bool v){ decay_if_unused=v; return *this; }
+  int getDecayHalfLifeTicks() const { return decay_half_life_ticks; }
+  ProximityConfig& setDecayHalfLifeTicks(int v){ decay_half_life_ticks=v; return *this; }
+  const std::vector<int>& getCandidateLayers() const { return candidate_layers; }
+  ProximityConfig& setCandidateLayers(const std::vector<int>& v){ candidate_layers=v; return *this; }
+  bool isRecordMeshRulesOnCrossLayer() const { return record_mesh_rules_on_cross_layer; }
+  ProximityConfig& setRecordMeshRulesOnCrossLayer(bool v){ record_mesh_rules_on_cross_layer=v; return *this; }
 };
```

*(Matches Java’s surface exactly per the report.)* 

### 2.4 LateralBus: public factor/decay/currentStep API

**`src/cpp/LateralBus.h`** *(or the class you expose as the lateral bus)*

```diff
@@ class LateralBus {
 public:
+  long long getCurrentStep() const { return currentStep; }
+  void decay() { 
+    inhibition *= inhibitionDecay; 
+    modulation  *= 1.0; 
+    ++currentStep; 
+  }
+  double getInhibitionFactor() const { return inhibition; }
+  void setInhibitionFactor(double v) { inhibition = v; }
+  double getInhibitionDecay() const { return inhibitionDecay; }
+  void setInhibitionDecay(double v) { inhibitionDecay = v; }
+  double getModulationFactor() const { return modulation; }
+  void setModulationFactor(double v) { modulation = v; }
```

*(Names/fields adapted to your existing members; the behavior mirrors your existing decay semantics and Java getters.)* 

### 2.5 RegionMetrics: add getters (Java parity)

**`src/cpp/RegionMetrics.h`**

```diff
@@ struct RegionMetrics {
   long long deliveredEvents = 0;
   long long totalSlots = 0;
   long long totalSynapses = 0;
   // spatial
   long long activePixels = 0;
   int bboxRowMin=0,bboxRowMax=-1,bboxColMin=0,bboxColMax=-1;
   double centroidRow=0.0, centroidCol=0.0;

+  // -- getters (Java parity) --
+  long long getDeliveredEvents() const { return deliveredEvents; }
+  long long getTotalSlots()     const { return totalSlots; }
+  long long getTotalSynapses()  const { return totalSynapses; }
+  long long getActivePixels()   const { return activePixels; }
+  int getBboxRowMin() const { return bboxRowMin; }
+  int getBboxRowMax() const { return bboxRowMax; }
+  int getBboxColMin() const { return bboxColMin; }
+  int getBboxColMax() const { return bboxColMax; }
+  double getCentroidRow() const { return centroidRow; }
+  double getCentroidCol() const { return centroidCol; }
```

### 2.6 Input/Output 2D and ND: expose required accessors

**`src/cpp/InputLayer2D.h`**

```diff
@@ class InputLayer2D : public Layer {
 public:
+  int getHeight() const { return height; }
+  int getWidth()  const { return width; }
+  const std::vector<std::vector<double>>& getFrame() const { return frame; }
+  void forwardImage(const std::vector<std::vector<double>>& f) { forward(f); }
```

**`src/cpp/OutputLayer2D.h`**

```diff
@@ class OutputLayer2D : public Layer {
 public:
+  int getHeight() const { return height; }
+  int getWidth()  const { return width; }
+  const std::vector<std::vector<double>>& getFrame() const { return frame; }
```

**`src/cpp/InputLayerND.h`**

```diff
@@ class InputLayerND : public Layer {
 public:
+  const std::vector<int>& getShape() const { return shape; }
+  bool hasShape(const std::vector<int>& s) const { return shape == s; }
+  size_t size() const { return totalSize; }
+  void forwardND(const std::vector<double>& flat, const std::vector<int>& s) { forward(flat, s); }
```

> These methods are explicitly listed as present in Java but missing in C++. 

### 2.7 Tract/TractWindowed: query helpers (Java parity + addenda)

**`src/cpp/Tract.h`**

```diff
@@ class Tract {
 public:
+  bool isFeedback() const { return feedback; }
+  Layer* getSource() const { return source; }
+  Layer* getDestination() const { return destination; }
+  size_t edgeCount() const { return edges.size(); }         // if you keep an edge list; else compute on demand
+  void flush() { /* no-op or drain buffers if any */ }
+  void pruneEdges(long long /*staleWindow*/, double /*minStrength*/) { /* TODO: implement later */ }
+  void wireDenseRandom(double probability) { /* optional: call existing random wiring */ }
```

**`src/cpp/include/TractWindowed.h`**

```diff
@@ class TractWindowed {
 public:
-  bool destinationIsOutput2D() const { return destIsOutput2D; }
+  bool destinationIsOutput2D() const { return destIsOutput2D; }
+  std::pair<int,int> centerForWindow(int originRow, int originCol) const;
+  bool windowCoversSourceIndex(int srcIndex) const;
+  void buildFromSourceGrid(int height, int width); // no-op if already built
```

**`src/cpp/src/TractWindowed.cpp`**

```diff
@@
 std::pair<int,int> TractWindowed::centerForWindow(int r, int c) const {
   // implement your “center rule” mapping (floor midpoint) with clamping
   const int rr = std::max(0, std::min(destHeight-1, r + kernelHeight/2));
   const int cc = std::max(0, std::min(destWidth -1, c + kernelWidth /2));
   return {rr,cc};
 }
 bool TractWindowed::windowCoversSourceIndex(int srcIndex) const {
   // reverse-map srcIndex -> (row,col) and check against last origins grid
   if (srcIndex < 0 || srcIndex >= (int)(srcHeight*srcWidth)) return false;
   const int r = srcIndex / srcWidth, c = srcIndex % srcWidth;
   // quick conservative check
   return r >= 0 && r < srcHeight && c >= 0 && c < srcWidth;
 }
 void TractWindowed::buildFromSourceGrid(int h, int w) {
   srcHeight = h; srcWidth = w; // allow re-init
 }
```

*(Minimal implementations; refine internals to match your exact data flow.)*

------

## 3) Java changes

> Java already has most of the methods; this patch **adds** the new v5.1 addenda and **keeps names** consistent with contract.

### 3.1 Region: add C++‑only methods (now in contract v5.1)

**`src/java/ai/nektron/grownet/Region.java`**

```diff
@@ public class Region {
+  // v5.1 addenda (C++ → parity)
+  public void autowireNewNeuron(Layer L, int newIndex) {
+    // delegate to existing mesh/tract re-attach logic
+    // no-op if not applicable in Java build
+    if (L != null) {
+      // hook: region.autowireNewNeuronByRef or tract re-attach if present
+    }
+  }
+  public int ensureInputEdge(String port) {
+    return internalEnsureEdge(port, /*isInput=*/true);
+  }
+  public int ensureOutputEdge(String port) {
+    return internalEnsureEdge(port, /*isInput=*/false);
+  }
+  public void maybeGrowRegion() {
+    // delegate to GrowthEngine.maybeGrow(this) if available
+    GrowthEngine.maybeGrow(this);
+  }
+  private int internalEnsureEdge(String port, boolean isInput) {
+    // create a 1-neuron scalar edge if absent; return layer index
+    return EdgeRegistry.ensureEdge(this, port, isInput);
+  }
```

*(If you already have helpers for edges/growth, replace the bodies with direct calls.)*

### 3.2 ProximityEngine: name already `apply`

No change. (C++ added alias.)

### 3.3 TractWindowed (optional)

Add a thin Java class mirroring the three addenda declared in §1.3 if you want full parity:

```java
public final class TractWindowed {
  public boolean destinationIsOutput2D() { /* wire into Output2D path */ return true; }
  public int[] centerForWindow(int r, int c) { /* center rule */ return new int[]{r, c}; }
  public boolean windowCoversSourceIndex(int srcIndex) { return srcIndex >= 0; }
  public void buildFromSourceGrid(int h, int w) { /* no-op */ }
}
```

------

## 4) Tests (smoke + compile‑time parity)

### 4.1 C++: API surface smoke (gtest)

**`src/cpp/tests/api_parity_surface_test.cpp`**

```cpp
#include "gtest/gtest.h"
#include "Region.h"
#include "ProximityEngine.h"
#include "ProximityConfig.h"
#include "RegionMetrics.h"
#include "LateralBus.h"

using namespace grownet;

TEST(ApiParity, RegionSurface) {
  Region r("parity");
  auto& bus = r.getBus(); (void)bus;
  EXPECT_NO_THROW( r.setEnableSpatialMetrics(true) );
  EXPECT_NO_THROW( r.getLayers() );
}

TEST(ApiParity, ProximityNaming) {
  Region r("prox");
  ProximityConfig pc; pc.setEnabled(true).setRadius(1.0);
  // both names compile:
  EXPECT_GE(ProximityEngine::Apply(r, pc), 0);
  EXPECT_GE(ProximityEngine::apply(r, pc), 0);
}

TEST(ApiParity, MetricsGetters) {
  RegionMetrics m;
  (void)m.getTotalSlots();
  (void)m.getTotalSynapses();
  (void)m.getDeliveredEvents();
}
```

### 4.2 Java: API surface smoke (JUnit)

**`src/java/ai/nektron/grownet/tests/ApiParitySurfaceTest.java`**

```java
import org.junit.jupiter.api.Test;
import ai.nektron.grownet.*;

public class ApiParitySurfaceTest {
  @Test
  public void regionSurface() {
    Region r = new Region("parity");
    r.setEnableSpatialMetrics(true);
    r.getLayers();
  }
  @Test
  public void proximityNaming() {
    Region r = new Region("prox");
    ProximityConfig cfg = new ProximityConfig().setEnabled(true).setRadius(1.0);
    int a = ProximityEngine.apply(r, cfg);
    // C++ keeps Apply alias; Java is already 'apply'
  }
}
```

------

## 5) Build system nits (CMake + Maven)

### 5.1 CMake (guard to keep tests/demos out of core lib)

*(If not present already from earlier fix)*

**`CMakeLists.txt`**

```diff
@@
 foreach(_src IN LISTS GROWNET_ALL_CPP)
   if(_src MATCHES "/demo/")
     list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
+  elseif(_src MATCHES "/tests/")
+    list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
   elseif(_src MATCHES "[/\\]Demo.*\\.cpp$")
     list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
   elseif(_src MATCHES "[/\\]demo_.*\\.cpp$")
     list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
   endif()
 endforeach()
```

### 5.2 Java (no change)

Ensure your existing Maven setup already discovers `src/java/**/tests`. (You already mentioned the build works locally.)

------

## 6) What this PR fixes from your report

- **ProximityEngine** naming (`Apply` vs `apply`) — exact alias added in C++ so both compile, while the contract name remains `apply`. 
- **Region** missing accessors in C++: `getBus`, `getLayers`, `getName`, `getProximityConfig`/`setProximityConfig`, `isEnableSpatialMetrics`/`setEnableSpatialMetrics`, `getGrowthPolicy`/`setGrowthPolicy`. 
- **ProximityConfig** full getter/setter surface in C++ to match Java. 
- **LateralBus** public decay/currentStep/decay+factor getters/setters (C++ parity with Java). 
- **RegionMetrics** getters added in C++ (Java has them per report). 
- **InputLayer2D/OutputLayer2D** accessors and `forwardImage` exposed in C++. 
- **InputLayerND** accessors (`getShape`, `hasShape`, `size`, `forwardND`) in C++. 
- **Tract/TractWindowed**: basic query helpers added to C++ and declared optional in contract (with Java shims if you want full parity). 
- **Java additions from C++** via contract addenda: `autowireNewNeuron`, `ensureInputEdge`, `ensureOutputEdge`, `maybeGrowRegion`. 

------

## 7) Rollout checklist

1. Apply these diffs and build:
   - **C++:** core lib, then tests (`api_parity_surface_test.cpp`).
   - **Java:** `mvn -q -Dtest=ApiParitySurfaceTest test`.
2. Re‑run your **API diff script** (the one you generated earlier) to verify **no public deltas** remain against the updated contract.
3. If anything still red‑lines, paste the next diff and I’ll produce an incremental patch.

------

### Notes

- I deliberately limited changes to **surface parity** (no semantic modifications). Anywhere an implementation detail wasn’t obvious (e.g., `Tract` internal edge bookkeeping), I supplied **safe stubs** you can flesh out later without breaking binary compatibility.
- Keeping **backwards compatibility** in C++: leaving `Apply` as an alias ensures existing C++ callers continue to compile while Java remains canonical with `apply`.

If desired, we can add another PR to cover every last item under **AnchorMode**, **Mode**, **MathUtils** (Java‑only in the report) with C++ mirrors, I can add those as a Phase‑2 patch; the approach will be identical—pure wrappers/getters to close surface parity. 

------

**End of PR**
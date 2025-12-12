# Creation and Growth Points (Python, TypeScript, C++, Java, Mojo)

This doc shows where core elements are created/instantiated and where growth happens in the codebase. It focuses on Slots (allocation in selectors), Neuron growth, Layer creation/growth, and Region growth. Snippets include the key lines and file references for quick navigation.

## Cross‑Language Summary (Growth Ladder)

```
Slots (per‑neuron) → Neurons (per‑layer) → Layers (per‑region) → Region (policy)
```

- Slots (create): when desired bin/key is missing AND under `slot_limit`; at capacity, reuse fallback deterministically and mark `last_slot_used_fallback = true`.
- Neuron (grow): strict capacity AND last select used fallback AND `fallback_streak ≥ threshold` AND `cooldown` satisfied.
- Layer (spillover): called when a layer hits `neuron_limit` (and is allowed); add a small new layer; wire donor → new with `p = 1.0`.
- Region (policy): OR‑trigger on pressure (avg slots or % at‑cap+fallback) and cooldown; add at most one layer per tick; wire donor → new with `p = 1.0`.

## Python

### Slot creation (strict capacity + fallback)
- File: `src/python/slot_engine.py:60`
```python
# Ensure existence (respect capacity)
if sid not in slots:
    if at_capacity:
        if not slots:
            slots[sid] = Weight()
    else:
        slots[sid] = Weight()
```

Conditions (plain English)
- Create a new slot when the desired bin is missing AND `len(slots) < effective slot_limit`.
- Do not create at capacity. If desired is out-of-domain or new-while-at-capacity → reuse a deterministic fallback id and set `last_slot_used_fallback = True`.
- Bootstrap exception: if at-capacity but there are zero slots, create one.

### Neuron growth trigger (fallback streak + cooldown → Layer.try_grow_neuron)
- File: `src/python/neuron.py:248`
```python
if self.fallback_streak >= max(1, threshold) and self.owner is not None:
    now = int(self.bus.get_current_step()) if self.bus is not None else 0
    cooldown = int(getattr(cfg, "neuron_growth_cooldown_ticks", 10))
    if self.last_growth_tick is None or (now - int(self.last_growth_tick)) >= cooldown:
        self.owner.try_grow_neuron(self)
        self.last_growth_tick = now
```

Conditions (plain English)
- Per‑neuron growth is enabled: `slot_cfg.growth_enabled` AND `slot_cfg.neuron_growth_enabled`.
- Strict capacity: `len(slots) ≥ effective slot_limit`.
- The last selection used a fallback bin: `last_slot_used_fallback == True`.
- Fallback streak threshold: `fallback_streak ≥ slot_cfg.fallback_growth_threshold` (default 3).
- Cooldown: `bus.current_step − last_growth_tick ≥ slot_cfg.neuron_growth_cooldown_ticks` (default 0).
- Optional guards (if present): `min_delta_pct_for_growth` and `fallback_growth_requires_same_missing_slot`.

### Layer adds a neuron (clones seed + autowires)
- File: `src/python/layer.py:107`
```python
def try_grow_neuron(self, seed_neuron) -> int | None:
    # … cap checks …
    new_n = cls(name)
    new_n.set_bus(self.bus)
    new_n.slot_cfg = seed_neuron.slot_cfg
    new_n.slot_engine = SlotEngine(new_n.slot_cfg)
    new_n.slot_limit = seed_neuron.slot_limit
    new_n.owner = self
    self.neurons.append(new_n)
    if self.region is not None:
        self.region.autowire_new_neuron(self, len(self.neurons) - 1)
```

Conditions (plain English)
- Per‑layer cap honored: if `neuron_limit` is set and reached, block neuron growth and optionally escalate to layer growth (see below) if `seed_neuron.slot_cfg.layer_growth_enabled == True`.
- New neuron is same kind as seed; bus/config/limits copied; owner set; region autowires via mesh rules/tracts.

### Layer creation (Region API)
- File: `src/python/region.py:53`
```python
def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
    from layer import Layer
    layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
    layer.set_region(self)
    self.layers.append(layer)
    return len(self.layers) - 1
```

Creation (plain English)
- Adds a mixed E/I/M layer; sets region back‑ref for growth/autowiring.

### Layer growth (spillover) and autowiring
- File: `src/python/region.py:287`
```python
def request_layer_growth(self, saturated_layer) -> int | None:
    idx = self.layers.index(saturated_layer)
    new_exc = max(4, (getattr(saturated_layer, 'excitatory_count', 4) // 2) or 4)
    new_idx = self.add_layer(excitatory_count=new_exc, inhibitory_count=0, modulatory_count=0)
    self.connect_layers(idx, new_idx, probability=1.0, feedback=False)
    return new_idx
```

Conditions (plain English)
- Called explicitly (e.g., when a layer hits `neuron_limit` and `layer_growth_enabled` is True on the requesting neuron).
- Deterministic wiring: connect saturated → new with `p = 1.0`.

### Region growth (policy-driven; OR trigger)
- File: `src/python/growth.py:40`
```python
def maybe_grow(region, policy: Optional[GrowthPolicy]) -> bool:
    # compute avg_slots and % at-cap+fallback …
    if avg_slots_per_neuron >= policy.avg_slots_threshold or pct_saturated >= policy.percent_neurons_at_cap_threshold:
        new_index = region.add_layer(excitatory_count=new_e, inhibitory_count=0, modulatory_count=0)
        region.connect_layers(best_layer_index, new_index, probability=float(policy.wire_probability), feedback=False)
        setattr(region, "last_layer_growth_step", now)
        return True
    return False
```

Conditions (plain English)
- Policy enabled; not past `max_total_layers`.
- Cooldown respected: `region.bus/layer.bus current_step − last_layer_growth_step ≥ policy.layer_cooldown_ticks`.
- OR‑trigger: `avg_slots_per_neuron ≥ policy.avg_slots_threshold` OR `% at capacity AND using fallback ≥ policy.percent_neurons_at_cap_threshold`.
- Exactly one layer added per tick; wire donor → new with `p = 1.0`.

## TypeScript

### Slot creation (strict capacity + fallback)
- File: `src/typescript/grownet-ts/src/core/Neuron.ts:98`
```ts
const slot = this.selectOrCreateSlot(binIndex);
slot.reinforce(this.bus.getModulationFactor());
this.firedLast = slot.updateThreshold(value * this.bus.getModulationFactor());
```

Conditions (plain English)
- Create slot when desired key is missing AND `slots.size < slotLimit`.
- At capacity: never create; reuse a deterministic fallback and mark `lastSlotUsedFallback = true`.

### Neuron growth (fallback streak + cooldown; one per layer per tick)
- File: `src/typescript/grownet-ts/src/core/Layer.ts:43`
```ts
// Automatic neuron growth; one growth per layer per tick
let grownThisTick = false;
const threshold = this.slotConfig?.fallbackGrowthThreshold ?? 3;
const cooldownTicks = this.slotConfig?.neuronGrowthCooldownTicks ?? 0;
if (growthEnabled && neuronGrowthEnabled) {
  const currentStep = this.bus.getCurrentStep();
  for (let neuronIndex = 0; neuronIndex < this.neurons.length && !grownThisTick; neuronIndex += 1) {
    const neuron = this.neurons[neuronIndex] as any;
    const atCapacity = (neuron.getSlotLimit?.() ?? -1) >= 0 && (neuron.getSlotsCount?.() ?? 0) >= (neuron.getSlotLimit?.() ?? -1);
    const usedFallback = neuron.getLastSlotUsedFallback?.() ?? false;
    const streak = neuron.getFallbackStreak?.() ?? 0;
    const lastGrowth = neuron.getLastGrowthTick?.() ?? -1;
    const cooldownOk = lastGrowth < 0 || (currentStep - lastGrowth) >= cooldownTicks;
    if (atCapacity && usedFallback && streak >= threshold && cooldownOk) {
      const newIndex = this.tryGrowNeuron();
      if (newIndex >= 0) { neuron.setLastGrowthTick?.(currentStep); grownThisTick = true; }
    }
  }
}
```

Conditions (plain English)
- Growth is enabled: `slotConfig.growthEnabled` AND `slotConfig.neuronGrowthEnabled`.
- Strict capacity: `getSlotsCount() ≥ getSlotLimit()`.
- Fallback used on last selection: `getLastSlotUsedFallback() == true`.
- Fallback streak threshold: `getFallbackStreak() ≥ slotConfig.fallbackGrowthThreshold`.
- Cooldown: `bus.getCurrentStep() − getLastGrowthTick() ≥ slotConfig.neuronGrowthCooldownTicks`.
- Guard: only one neuron grown per layer per tick.

### Layer creation (Region API)
- File: `src/typescript/grownet-ts/src/Region.ts:24`
```ts
addLayer(excitatoryCount: number): number {
  const layerId = this.nextLayerId++;
  const layer = new Layer(`layer_${layerId}`, LayerKind.Generic);
  layer.addNeurons(Math.max(0, Math.floor(excitatoryCount)));
  layer.setRegion?.(this);
  this.layers.push(layer);
  return layerId;
}
```

Creation (plain English)
- Adds a generic Layer and instantiates `excitatoryCount` neurons; sets region back‑ref.

### Layer growth (spillover) and autowiring
- File: `src/typescript/grownet-ts/src/Region.ts:231`
```ts
requestLayerGrowth(saturatedLayerIndex: number, connectionProbability = 1.0): number {
  if (saturatedLayerIndex < 0 || saturatedLayerIndex >= this.layers.length) return -1;
  const newIdx = this.addLayer(4);
  this.connectLayers(saturatedLayerIndex, newIdx, connectionProbability, false);
  return newIdx;
}
```

Conditions (plain English)
- Called to add a spillover layer; connects saturated → new with probability `connectionProbability` (default 1.0) and replays mesh rules on subsequent neuron growth.

### Region growth (policy-driven; OR trigger)
- File: `src/typescript/grownet-ts/src/Region.ts:378`
```ts
// Phase B: end tick + region growth check (one growth per tick)
for (let layerIndexIter = 0; layerIndexIter < this.layers.length; layerIndexIter += 1) {
  const layerObj = this.layers[layerIndexIter];
  if (layerObj) layerObj.endTick();
}
if (this.growthPolicy && this.growthPolicy.enableLayerGrowth) {
  // compute avgSlots and % at-cap+fallback …
  if (avgOk || pctOk) {
    let donor = -1;
    for (let i = this.layers.length - 1; i >= 0; i -= 1) {
      const candidateLayer = this.layers[i];
      if (candidateLayer && this.isTrainable(candidateLayer.getKind())) { donor = i; break; }
    }
    if (donor >= 0) {
      const newIndex = this.requestLayerGrowth(donor, 1.0);
      if (newIndex >= 0) this.lastLayerGrowthStep = currentStep;
    }
  }
}
```

Conditions (plain English)
- Policy enabled; below `maxLayers`.
- Cooldown respected: `currentStep − lastLayerGrowthStep ≥ layerCooldownTicks`.
- OR‑trigger: `avgSlots ≥ avgSlotsThreshold` OR `% at-cap+fallback ≥ percentNeuronsAtCapacityThreshold`.
- Exactly one layer added per tick; wire donor → new with `p = 1.0`.

## C++

### Slot creation (strict capacity + fallback)
- File: `src/cpp/SlotEngine.cpp:34`
```cpp
auto iter = slots.find(sid);
if (iter == slots.end()) {
  if (atCapacity) {
    if (slots.empty()) { iter = slots.emplace(sid, Weight{}).first; }
    else { iter = slots.begin(); }
  } else {
    iter = slots.emplace(sid, Weight{}).first;
  }
}
```

Conditions (plain English)
- Create a slot when desired id is missing AND `slots.size() < limit`.
- At capacity: never create; if empty bootstrap, create; else reuse an existing slot deterministically; mark fallback.

### Layer creation (Region API)
- File: `src/cpp/Region.cpp:24`
```cpp
int Region::addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
  layers.push_back(std::make_shared<Layer>(excitatoryCount, inhibitoryCount, modulatoryCount));
  layers.back()->setRegionPtr(this);
  return static_cast<int>(layers.size() - 1);
}
```

Creation (plain English)
- Adds a mixed E/I/M layer; sets region pointer for growth/autowiring.

### Layer growth (spillover) and autowiring
- File: `src/cpp/Region.cpp:206`
```cpp
int Region::requestLayerGrowth(Layer* saturated) {
  int saturated_index = /* … find index … */;
  int new_layer_index = addLayer(4, 0, 0);
  connectLayers(saturated_index, new_layer_index, 1.0, false);
  return new_layer_index;
}
```

Conditions (plain English)
- Called explicitly or from policy; connect saturated → new with `p = 1.0`.

### Region growth (policy-driven; OR trigger)
- File: `src/cpp/Region.cpp:548`
```cpp
void Region::maybeGrowRegion() {
  if (!hasGrowthPolicy || !growthPolicy.enableRegionGrowth) return;
  // compute avgSlots and % at-cap+fallback …
  if (avgOk || pctOk) {
    int newIndex = requestLayerGrowth(layers[bestLayerIndex].get(), growthPolicy.connectionProbability);
    if (newIndex >= 0) lastRegionGrowthStep = currentStep;
  }
}
```

Conditions (plain English)
- Policy enabled; within `maximumLayers`.
- Cooldown respected: `currentStep − lastRegionGrowthStep ≥ layerCooldownTicks`.
- OR‑trigger: `avgSlots ≥ averageSlotsThreshold` OR `% at-cap+fallback ≥ percentAtCapFallbackThreshold`.
- Exactly one layer added per tick; wire donor → new with `p = 1.0`.

## Java

### Slot creation (strict capacity + fallback)
- File: `src/java/ai/nektron/grownet/SlotEngine.java:52`
```java
if (!neuron.getSlots().containsKey(sid)) {
  if (atCapacity) {
    if (neuron.getSlots().isEmpty()) {
      neuron.getSlots().put(sid, new Weight());
    }
  } else {
    neuron.getSlots().put(sid, new Weight());
  }
}
```

Conditions (plain English)
- Create slot when desired id is missing AND under `slotLimit`.
- At capacity: never create except on empty bootstrap; otherwise reuse; mark fallback.

### Layer creation (Region API)
- File: `src/java/ai/nektron/grownet/Region.java:36`
```java
public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
  Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
  try { layer.setRegion(this); } catch (Throwable ignored) {}
  layers.add(layer);
  return layers.size() - 1;
}
```

Creation (plain English)
- Adds a mixed layer and sets region back‑ref; used by Region and edge helpers.

### Region growth (policy-driven; OR trigger)
- File: `src/java/ai/nektron/grownet/growth/GrowthEngine.java:20`
```java
public static void maybeGrow(Region region, GrowthPolicy policy) {
  // compute avg slots and % at-cap+fallback …
  if (avgOk || pctOk) {
    int prev = layers.size() - 1;
    int newIndex = region.addLayer(Math.max(1, /* small */ (int)Math.round(Math.min(8, totalNeurons / Math.max(1.0, layers.size())))), 0, 0);
    if (prev >= 0) region.connectLayers(prev, newIndex, 1.0, false);
    policy.setLastLayerGrowthTick(tick);
  }
}
```

Conditions (plain English)
- Policy enabled; below `maxLayers`.
- Cooldown respected: `tick − lastLayerGrowthTick ≥ layerCooldownTicks`.
- OR‑trigger: `avgSlots ≥ avgSlotsThreshold` OR `% at-cap+fallback ≥ percentAtCapFallbackThreshold`.
- Exactly one layer added per tick; wire donor → new with `p = 1.0`.

## Mojo

### Slot creation (strict capacity + fallback)
- File: `src/mojo/slot_engine.mojo:60`
```mojo
if not neuron.slots.contains(selected_slot_id):
    if at_capacity:
        if neuron.slots.size() == 0:
            neuron.slots[selected_slot_id] = Weight()
    else:
        neuron.slots[selected_slot_id] = Weight()
```

Conditions (plain English)
- Create slot when desired id is missing AND under slot_limit.
- At capacity: never create; bootstrap if empty; otherwise reuse; mark fallback.

---

## Constructor Entry Points (by language)

- Python
  - Region: `src/python/region.py:17` (`class Region`) — orchestrates layers, ports, growth
  - Layer: `src/python/layer.py:8` (`class Layer`) — mixed E/I/M + LateralBus
  - Input/Output 2D: `src/python/input_layer_2d.py`, `src/python/output_layer_2d.py`

- TypeScript
  - Region: `src/typescript/grownet-ts/src/Region.ts:6` (`export class Region`)
  - Layer: `src/typescript/grownet-ts/src/core/Layer.ts:7` (`export class Layer`)
  - Neuron: `src/typescript/grownet-ts/src/core/Neuron.ts:5`

- C++
  - Region: `src/cpp/Region.h`, `src/cpp/Region.cpp:17` (`Region::Region`)
  - Layer: `src/cpp/Layer.h/cpp` (constructed via `Region::addLayer`)
  - Input/Output 2D: `src/cpp/InputLayer2D.h`, `src/cpp/OutputLayer2D.h`

- Java
  - Region: `src/java/ai/nektron/grownet/Region.java:22`
  - Layer: `src/java/ai/nektron/grownet/Layer.java` (constructed via `Region.addLayer`)
  - Input/Output 2D: `src/java/ai/nektron/grownet/InputLayer2D.java`, `OutputLayer2D.java`

- Mojo
  - Region: `src/mojo/region.mojo:21` (`struct Region`)
  - Layer/Neuron: `src/mojo/layer.mojo`, `src/mojo/neuron.mojo`

## Numeric Defaults Quick Reference

- Python SlotConfig (class defaults)
  - `slot_limit=16`, `bin_width_pct=10.0`, `epsilon_scale≈1e‑6`
  - `growth_enabled=True`, `neuron_growth_enabled=True`
  - `fallback_growth_threshold=3`, `neuron_growth_cooldown_ticks=0`

- TypeScript SlotConfig (fixedSlotConfig)
  - `slotLimit=-1` (unlimited unless set), `fallbackGrowthThreshold=3`
  - `neuronGrowthCooldownTicks=100` (demo‑friendly; can be overridden per neuron)

- C++ GrowthPolicy (defaults in header)
  - `averageSlotsThreshold=12.0`, `percentAtCapFallbackThreshold=0.0` (off)
  - `layerCooldownTicks=50`, `connectionProbability=1.0`

- Region policy (Python GrowthPolicy defaults in code)
  - `avg_slots_threshold=8.0`, `percent_neurons_at_cap_threshold=50.0`
  - `layer_cooldown_ticks=25`, `wire_probability=1.0`

Notes
- Defaults can vary per language and are often configured in tests/demos; the conditions above remain the same.


---

If you want a similar pass specifically on constructor entry points (e.g., Region/Layer object constructors) or a visual diagram of the growth ladder (Slots → Neurons → Layers → Regions) per language, I can add that as a follow-up.

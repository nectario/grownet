# GrowNet API Parity Report

**Inputs**

- C++ root: `../src/cpp`
- Java root: `../src/java`
- Contract YAML: `../GrowNet_Contract_v5_master.yaml` (NOT loaded)

## 3) Java ⇄ C++ parity

### Class `AnchorMode`
- ❗ Present in Java but missing in C++: adaptive/2, fixed/1, getAnchorBeta/0, getAnchorMode/0, getBinWidthPct/0, getEpsilonScale/0, getFallbackGrowthThreshold/0, getMinDeltaPctForGrowth/0, getNeuronGrowthCooldownTicks/0, getOutlierGrowthThresholdPct/0, getRecenterLockTicks/0, getRecenterThresholdPct/0, getSlotLimit/0, isFallbackGrowthRequiresSameMissingSlot/0, isGrowthEnabled/0, isNeuronGrowthEnabled/0, nonuniform/1, setAnchorBeta/1, setAnchorMode/1, setBinWidthPct/1, setEpsilonScale/1, setFallbackGrowthRequiresSameMissingSlot/1, setFallbackGrowthThreshold/1, setGrowthEnabled/1, setMinDeltaPctForGrowth/1, setNeuronGrowthCooldownTicks/1, setNeuronGrowthEnabled/1, setOutlierGrowthThresholdPct/1, setRecenterLockTicks/1, setRecenterThresholdPct/1, setSlotLimit/1, singleSlot/0

### Class `DemoMain`
- ❗ Present in Java but missing in C++: main/1

### Class `DeterministicLayout`
- ❗ Present in Java but missing in C++: position/5

### Class `GrowthEngine`
- ❗ Present in Java but missing in C++: maybeGrow/2, maybeGrowNeurons/2

### Class `GrowthPolicy`
- ❗ Present in Java but missing in C++: getAvgSlotsThreshold/0, getLastLayerGrowthTick/0, getLastNeuronGrowthTick/0, getLayerCooldownTicks/0, getMaxLayers/0, getNeuronCooldownTicks/0, getNeuronOutlierThresholdPct/0, getPercentAtCapFallbackThreshold/0, isEnableLayerGrowth/0, isEnableNeuronGrowth/0, setAvgSlotsThreshold/1, setEnableLayerGrowth/1, setEnableNeuronGrowth/1, setLastLayerGrowthTick/1, setLastNeuronGrowthTick/1, setLayerCooldownTicks/1, setMaxLayers/1, setNeuronCooldownTicks/1, setNeuronOutlierThresholdPct/1, setPercentAtCapFallbackThreshold/1

### Class `ImageIODemo`
- ❗ Present in Java but missing in C++: main/1

### Class `InhibitoryNeuron`
- ❗ Present in Java but missing in C++: getGamma/0, setGamma/1

### Class `InputLayer2D`
- ❗ Present in Java but missing in C++: forwardImage/1, getFrame/0, getHeight/0, getWidth/0, index/2, propagateFrom/2

### Class `InputLayerND`
- ❗ Present in Java but missing in C++: forwardND/2, getShape/0, hasShape/1, propagateFrom/2, size/0

### Class `InputNeuron`
- ❗ Present in Java but missing in C++: getOutputValue/0, onInput/1, onOutput/1

### Class `LateralBus`
- ❗ Present in Java but missing in C++: decay/0, getCurrentStep/0, getInhibitionDecay/0, getInhibitionFactor/0, getModulationFactor/0, setInhibitionDecay/1, setInhibitionFactor/1, setModulationFactor/1

### Class `Layer`
- ❗ Present in Java but missing in C++: endTick/0, forward/1, getBus/0, getNeurons/0, propagateFrom/2, setNeuronLimit/1, setRegion/1, tryGrowNeuron/1, wireRandomFeedback/1, wireRandomFeedforward/1

### Class `MathUtils`
- ❗ Present in Java but missing in C++: clamp/3, smoothClamp/3

### Class `Mode`
- ❗ Present in Java but missing in C++: defaults/0, getAdjustCooldownTicks/0, getAdjustFactorDown/0, getAdjustFactorUp/0, getBoundaryRefineHits/0, getMaxSlotWidth/0, getMinSlotWidth/0, getMode/0, getMultiresWidths/0, getNonuniformSchedule/0, getSlotWidthPercent/0, getTargetActiveHigh/0, getTargetActiveLow/0

### Class `ModulatoryNeuron`
- ❗ Present in Java but missing in C++: getKappa/0, setKappa/1

### Class `Neuron`
- ❗ Present in Java but missing in C++: connect/2, freezeLastSlot/0, getBus/0, getFocusAnchor/0, getId/0, getLastInputValue/0, getOutgoing/0, getSlotLimit/0, getSlots/0, neuronValue/1, onInput2D/3, pruneSynapses/2, registerFireHook/1, unfreezeLastSlot/0

### Class `OutputLayer2D`
- ❗ Present in Java but missing in C++: endTick/0, getFrame/0, getHeight/0, getWidth/0, index/2, propagateFrom/2

### Class `OutputNeuron`
- ❗ Present in Java but missing in C++: endTick/0, getOutputValue/0, onInput/1, onOutput/1

### Class `ProximityConfig`
- ❗ Present in Java but missing in C++: getCandidateLayers/0, getCooldownTicks/0, getDecayHalfLifeTicks/0, getDevelopmentWindowEnd/0, getDevelopmentWindowStart/0, getFunction/0, getLinearExponentGamma/0, getLogisticSteepnessK/0, getMaxEdgesPerTick/0, getRadius/0, getStabilizationHits/0, isDecayIfUnused/0, isEnabled/0, isRecordMeshRulesOnCrossLayer/0, setCandidateLayers/1, setCooldownTicks/1, setDecayHalfLifeTicks/1, setDecayIfUnused/1, setDevelopmentWindowEnd/1, setDevelopmentWindowStart/1, setEnabled/1, setFunction/1, setLinearExponentGamma/1, setLogisticSteepnessK/1, setMaxEdgesPerTick/1, setRadius/1, setRecordMeshRulesOnCrossLayer/1, setStabilizationHits/1

### Class `ProximityEngine`
- ❗ Present in C++ but missing in Java: Apply/2
- ❗ Present in Java but missing in C++: apply/2
- ℹ️  Names differ only by case or style (same arity):
  - Java:apply/2  ↔  C++:Apply/2

### Class `Region`
- ❗ Present in C++ but missing in Java: autowireNewNeuron/2, bindInput2D/5, ensureInputEdge/1, ensureOutputEdge/1, maybeGrowRegion/0
- ❗ Present in Java but missing in C++: connectLayers/3, connectLayersWindowed/8, getBus/0, getGrowthPolicy/0, getLayers/0, getName/0, getProximityConfig/0, isEnableSpatialMetrics/0, layers/0, setEnableSpatialMetrics/1, setGrowthPolicy/1, setProximityConfig/1

### Class `RegionDemo`
- ❗ Present in Java but missing in C++: main/1

### Class `RegionGrowthDemo`
- ❗ Present in Java but missing in C++: main/1

### Class `RegionMetrics`
- ❗ Present in Java but missing in C++: addDeliveredEvents/1, addSlots/1, addSynapses/1, getActivePixels/0, getBboxColMax/0, getBboxColMin/0, getBboxRowMax/0, getBboxRowMin/0, getCentroidCol/0, getCentroidRow/0, getDeliveredEvents/0, getTotalSlots/0, getTotalSynapses/0, incDeliveredEvents/0, merge/1, reset/0, setActivePixels/1, setBBox/4, setCentroid/2

### Class `SingleNeuronDemo`
- ❗ Present in Java but missing in C++: main/1

### Class `SlotEngine`
- ❗ Present in C++ but missing in Java: selectOrCreateSlot/2, selectOrCreateSlot2D/3, slotId2D/4
- ❗ Present in Java but missing in C++: getConfig/0, selectOrCreateSlot/3, selectOrCreateSlot2D/4, slotId/3

### Class `SlotPolicy`
- ❗ Present in Java but missing in C++: slotId/3

### Class `SlotPolicyEngine`
- ❗ Present in Java but missing in C++: computePercentDelta/2, selectOrCreateSlot/3

### Class `SpatialHash`
- ❗ Present in Java but missing in C++: insert/3, near/1

### Class `Synapse`
- ❗ Present in Java but missing in C++: getLastStep/0, getTarget/0, getWeight/0, isFeedback/0, setLastStep/1

### Class `TestSingleTick`
- ❗ Present in Java but missing in C++: main/1

### Class `TopographicConfig`
- ❗ Present in Java but missing in C++: setFeedback/1, setKernel/2, setNormalizeIncoming/1, setPadding/1, setSigmaCenter/1, setSigmaSurround/1, setStride/2, setSurroundRatio/1, setWeightMode/1

### Class `TopographicWiring`
- ❗ Present in Java but missing in C++: connectLayersTopographic/4, incomingSums/2

### Class `Tract`
- ❗ Present in Java but missing in C++: edgeCount/0, flush/0, getDestination/0, getSource/0, isFeedback/0, pruneEdges/2, wireDenseRandom/1

### Class `TractWindowed`
- ❗ Present in C++ but missing in Java: buildFromSourceGrid/2, centerForWindow/2, windowCoversSourceIndex/1

### Class `Weight`
- ❗ Present in Java but missing in C++: freeze/0, getEmaRate/0, getReinforcementCount/0, getStepValue/0, getStrengthValue/0, getThresholdValue/0, hasSeenFirst/0, isFrozen/0, reinforce/1, setStepValue/1, unfreeze/0, updateThreshold/1

### Class `std`
- ❗ Present in C++ but missing in Java: invalid_argument/1, out_of_range/1, sqrt/1


## 4) Rename suggestions (heuristics)

- If you see items like `addInput2DLayer/2` vs `addInputLayer2D/2`, prefer a single canonical name 
  across both languages (contract v5). Consider adding a thin overload/alias temporarily.
- For case-only differences (e.g., `tick2D` vs `tick2d`), align to the contract’s spelling exactly.


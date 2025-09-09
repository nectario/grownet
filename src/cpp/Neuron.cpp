#include "Neuron.h"
#include "Layer.h"

namespace grownet {

bool Neuron::onInput(double value) {
    Weight& weight = slotEngine.selectOrCreateSlot(*this, value);
    weight.reinforce(getBus().getModulationFactor());
    bool fired = weight.updateThreshold(value);
    setFiredLast(fired);
    setLastInputValue(value);
    // Best-effort growth trigger with optional guards
    try {
        const SlotConfig& C = slotEngine.getConfig();
        if (C.growthEnabled && C.neuronGrowthEnabled) {
            const int limit = getSlotLimit();
            const bool atCap = (limit >= 0) && (static_cast<int>(getSlots().size()) >= limit);
            if (!(atCap && getLastSlotUsedFallback())) {
                setFallbackStreak(0);
                setPrevMissingSlotId(-1);
                setLastMissingSlotId(-1);
                return fired;
            }
            if (C.minDeltaPctForGrowth > 0.0) {
                if (getLastMaxAxisDeltaPct() < C.minDeltaPctForGrowth) {
                    setFallbackStreak(0);
                    setPrevMissingSlotId(-1);
                    return fired;
                }
            }
            if (C.fallbackGrowthRequiresSameMissingSlot) {
                if (getPrevMissingSlotId() == getLastMissingSlotId()) {
                    setFallbackStreak(getFallbackStreak() + 1);
                } else {
                    setFallbackStreak(1);
                    setPrevMissingSlotId(getLastMissingSlotId());
                }
            } else {
                setFallbackStreak(getFallbackStreak() + 1);
            }
            const int threshold = (C.fallbackGrowthThreshold < 1 ? 1 : C.fallbackGrowthThreshold);
            if (owner != nullptr && getFallbackStreak() >= threshold) {
                const long long now = getBus().getCurrentStep();
                const int cooldown = (C.neuronGrowthCooldownTicks < 0 ? 0 : C.neuronGrowthCooldownTicks);
                if (lastGrowthTick < 0 || (now - lastGrowthTick) >= cooldown) {
                    auto* L = reinterpret_cast<Layer*>(owner);
                    if (L) (void)L->tryGrowNeuron(*this);
                    lastGrowthTick = now;
                }
                setFallbackStreak(0);
                setPrevMissingSlotId(-1);
                setLastMissingSlotId(-1);
            }
        }
    } catch (...) { /* best-effort; swallow */ }
    return fired;
}

void Neuron::onOutput(double amplitude) {
    // Notify hooks (e.g., Tract) and then perform default excitatory fanout.
    notifyFire(amplitude);
    // Default excitatory fanout: deliver to connected targets
    for (auto& syn : outgoing) {
        if (syn.target) {
            bool downstreamFired = syn.target->onInput(amplitude);
            if (downstreamFired) syn.target->onOutput(amplitude);
        }
    }
}

} // namespace grownet

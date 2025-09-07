#include "Neuron.h"
#include "Layer.h"

namespace grownet {

bool Neuron::onInput(double value) {
    Weight& weight = slotEngine.selectOrCreateSlot(*this, value);
    weight.reinforce(getBus().getModulationFactor());
    bool fired = weight.updateThreshold(value);
    setFiredLast(fired);
    setLastInputValue(value);
    // Best-effort growth trigger: at-capacity + fallback streak with config-driven cooldown
    try {
        const SlotConfig& C = slotEngine.getConfig();
        const bool growthEnabled = C.growthEnabled;
        const bool neuronGrowthEnabled = C.neuronGrowthEnabled;
        if (growthEnabled && neuronGrowthEnabled) {
            const int limit = getSlotLimit();
            const bool atCap = (limit >= 0) && (static_cast<int>(getSlots().size()) >= limit);
            if (atCap && getLastSlotUsedFallback()) {
                fallbackStreak += 1;
            } else {
                fallbackStreak = 0;
            }
            const int threshold = (C.fallbackGrowthThreshold < 1 ? 1 : C.fallbackGrowthThreshold);
            if (owner != nullptr && fallbackStreak >= threshold) {
                const long long now = getBus().getCurrentStep();
                const int cooldown = (C.neuronGrowthCooldownTicks < 0 ? 0 : C.neuronGrowthCooldownTicks);
                if (lastGrowthTick < 0 || (now - lastGrowthTick) >= cooldown) {
                    // Call back into owner layer to add a neuron of same kind
                    auto* L = reinterpret_cast<Layer*>(owner);
                    if (L) (void)L->tryGrowNeuron(*this);
                    lastGrowthTick = now;
                }
                fallbackStreak = 0;
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

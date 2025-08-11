#include "Neuron.h"

namespace grownet {

double Neuron::computePercentDelta(double previous, double current) const {
    if (previous == 0.0) return 1.0;
    return std::abs(current - previous) / std::max(1e-9, std::abs(previous));
}

int Neuron::selectOrCreateSlotId(double value) {
    const double previous = hasLastInput ? lastInputValue : 0.0;
    double percent = computePercentDelta(previous, value);
    double width = (slotPolicy ? slotPolicy->slotWidthPercent : 0.10);

    // Active slots
    int active = 0;
    for (auto & kv : slots) if (kv.second.getHitCount() > 0) active++;

    // Adaptive cooldown uses bus->getCurrentStep() if available
    long long tick = bus ? bus->getCurrentStep() : 0;
    if (slotPolicy && slotPolicy->mode == SlotPolicyConfig::ADAPTIVE) {
        if (tick - policyLastAdjustTick >= slotPolicy->adjustCooldownTicks) {
            if (active > slotPolicy->targetActiveHigh) {
                width = std::min(slotPolicy->maxSlotWidth, width * slotPolicy->adjustFactorUp);
                policyLastAdjustTick = tick;
            } else if (active < slotPolicy->targetActiveLow && percent > width) {
                width = std::max(slotPolicy->minSlotWidth, width * slotPolicy->adjustFactorDown);
                policyLastAdjustTick = tick;
            }
        }
    }

    std::vector<double> widths;
    if (slotPolicy && slotPolicy->mode == SlotPolicyConfig::MULTI_RESOLUTION) widths = slotPolicy->multiresWidths;
    else widths = { width };

    for (double w : widths) {
        int bucket = (int) std::floor(percent / std::max(1e-9, w));
        if (slots.find(bucket) != slots.end()) return bucket;
    }
    if (widths.size() > 1) {
        for (size_t i=1; i<widths.size(); ++i) {
            int bucket = (int) std::floor(percent / std::max(1e-9, widths[i]));
            if (slots.find(bucket) != slots.end()) return bucket;
        }
    }

    double useW = widths.back();
    if (slotPolicy && !slotPolicy->nonuniformSchedule.empty()){
        size_t idx = slots.size();
        if (idx < slotPolicy->nonuniformSchedule.size()) useW = slotPolicy->nonuniformSchedule[idx];
    }
    int newId = (int) std::floor(percent / std::max(1e-9, useW));
    if (slotLimit >= 0 && (int)slots.size() >= slotLimit) {
        return slots.begin()->first; // reuse first slot
    }
    slots.emplace(newId, Weight{});
    return newId;
}


int Neuron::slotLimit = -1; // unlimited by default

void Neuron::onInput(double inputValue) {
    Weight& slot = selectSlot(inputValue);

    slot.reinforce(bus->getModulationFactor(), bus->getInhibitionFactor());

    if (slot.updateThreshold(inputValue)) {
        fire(inputValue);
    }

    hasLastInput = true;
    lastInputValue = inputValue;
}

Synapse* Neuron::connect(Neuron* target, bool isFeedback) {
    outgoing.emplace_back(target, isFeedback);
    return &outgoing.back();
}

void Neuron::pruneSynapses(long long currentStep, long long staleWindow, double minStrength) {
    auto keepPredicate = [&](const Synapse& synapse) -> bool {
        const bool staleTooLong = (currentStep - synapse.lastStep) > staleWindow;
        const bool weakStrength = synapse.getWeight().getStrengthValue() < minStrength;
        return !(staleTooLong && weakStrength);
    };
    outgoing.erase(
        std::remove_if(outgoing.begin(), outgoing.end(),
            [&](const Synapse& s){ return !keepPredicate(s); }),
        outgoing.end()
    );
}

void Neuron::fire(double inputValue) {
    for (Synapse& synapse : outgoing) {
        synapse.getWeight().reinforce(
            bus->getModulationFactor(), bus->getInhibitionFactor()
        );
        synapse.lastStep = bus->getCurrentStep();
        if (synapse.getWeight().updateThreshold(inputValue)) {
            if (synapse.getTarget() != nullptr) {
                synapse.getTarget()->onInput(inputValue);
            }
        }
    }
    // After you finish intra-layer propagation over outgoing synapses:
    for (const auto& hook : fireHooks) {
        hook(inputValue, *this);
    }
}

double Neuron::neuronValue(const std::string& mode) const {
    if (slots.empty()) return 0.0;

    if (mode == "readiness") {
        double bestMargin = -1e300;
        for (const auto& entry : slots) {
            const Weight& w = entry.second;
            const double margin = w.getStrengthValue() - w.getThresholdValue();
            if (margin > bestMargin) bestMargin = margin;
        }
        return bestMargin;
    } else if (mode == "firing_rate") {
        double sumRates = 0.0;
        for (const auto& entry : slots) {
            sumRates += entry.second.getEmaRate();
        }
        return sumRates / static_cast<double>(slots.size());
    } else if (mode == "memory") {
        double sumAbsStrength = 0.0;
        for (const auto& entry : slots) {
            sumAbsStrength += std::abs(entry.second.getStrengthValue());
        }
        return sumAbsStrength;
    }
    // Unknown mode -> default to readiness
    double bestMargin = -1e300;
    for (const auto& entry : slots) {
        const Weight& w = entry.second;
        const double margin = w.getStrengthValue() - w.getThresholdValue();
        if (margin > bestMargin) bestMargin = margin;
    }
    return bestMargin;
}

Weight& Neuron::selectSlot(double inputValue) {
    int slotId = selectOrCreateSlotId(inputValue);
    return slots.find(slotId)->second;
}

    auto found = slots.find(binId);
    if (found == slots.end()) {
        if (slotLimit >= 0 && static_cast<int>(slots.size()) >= slotLimit) {
            // reuse the first available slot (simple policy)
            return slots.begin()->second;
        } else {
            auto inserted = slots.emplace(binId, Weight{});
            return inserted.first->second;
        }
    }
    return found->second;
}

} // namespace grownet

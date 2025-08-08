#include "Neuron.h"

namespace grownet {

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
    int binId = 0;
    if (hasLastInput && lastInputValue != 0.0) {
        const double delta = std::abs(inputValue - lastInputValue) / std::abs(lastInputValue);
        const double deltaPercent = delta * 100.0;
        binId = (deltaPercent == 0.0) ? 0 : static_cast<int>(std::ceil(deltaPercent / 10.0));
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

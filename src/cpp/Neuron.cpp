
#include "Neuron.h"

namespace grownet {

int Neuron::slotLimit = -1;

void Neuron::onInput(double inputValue) {
    Weight& slot = selectSlot(inputValue);

    slot.reinforce(bus ? bus->getModulationFactor() : 1.0,
                   bus ? bus->getInhibitionFactor() : 0.0);

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

void Neuron::pruneSynapses(std::int64_t currentStep, std::int64_t staleWindow, double minStrength) {
    auto keep = [&](const Synapse& s) {
        bool staleTooLong = (currentStep - s.lastStep) > staleWindow;
        bool weakStrength = s.getWeight().getStrengthValue() < minStrength;
        return !(staleTooLong && weakStrength);
    };
    outgoing.erase(std::remove_if(outgoing.begin(), outgoing.end(),
                                  [&](const Synapse& s){ return !keep(s); }),
                   outgoing.end());
}

void Neuron::fire(double inputValue) {
    for (Synapse& s : outgoing) {
        if (bus) {
            s.getWeight().reinforce(bus->getModulationFactor(), bus->getInhibitionFactor());
            s.lastStep = bus->getCurrentStep();
        }
        if (s.getWeight().updateThreshold(inputValue)) {
            if (s.getTarget()) {
                s.getTarget()->onInput(inputValue);
            }
        }
    }
    // fire hooks (e.g., logging/visualization)
    for (const auto& hook : fireHooks) {
        hook(inputValue, *this);
    }
}

double Neuron::neuronValue(const std::string& mode) const {
    if (slots.empty()) return 0.0;

    if (mode == "readiness") {
        double bestMargin = -1e300;
        for (const auto& kv : slots) {
            const Weight& w = kv.second;
            double margin = w.getStrengthValue() - w.getThresholdValue();
            if (margin > bestMargin) bestMargin = margin;
        }
        return bestMargin;
    } else if (mode == "firing_rate") {
        double sumRates = 0.0;
        for (const auto& kv : slots) sumRates += kv.second.getEmaRate();
        return sumRates / static_cast<double>(slots.size());
    } else if (mode == "memory") {
        double sumAbsStrength = 0.0;
        for (const auto& kv : slots) sumAbsStrength += std::abs(kv.second.getStrengthValue());
        return sumAbsStrength;
    }

    // default to readiness
    double bestMargin = -1e300;
    for (const auto& kv : slots) {
        const Weight& w = kv.second;
        double margin = w.getStrengthValue() - w.getThresholdValue();
        if (margin > bestMargin) bestMargin = margin;
    }
    return bestMargin;
}

Weight& Neuron::selectSlot(double inputValue) {
    int binId = 0;
    if (hasLastInput && lastInputValue != 0.0) {
        double delta = std::abs(inputValue - lastInputValue) / std::abs(lastInputValue);
        double deltaPercent = delta * 100.0;
        binId = (deltaPercent == 0.0) ? 0 : static_cast<int>(std::ceil(deltaPercent / 10.0));
    }

    auto it = slots.find(binId);
    if (it == slots.end()) {
        if (slotLimit >= 0 && static_cast<int>(slots.size()) >= slotLimit) {
            return slots.begin()->second; // simple reuse policy
        } else {
            auto ins = slots.emplace(binId, Weight{});
            return ins.first->second;
        }
    }
    return it->second;
}

} // namespace grownet

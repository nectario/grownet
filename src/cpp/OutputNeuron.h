#pragma once
#include "Neuron.h"
#include "Weight.h"
#include "LateralBus.h"

namespace grownet {

class OutputNeuron : public Neuron {
public:
    explicit OutputNeuron(const std::string& name, double smoothing = 0.2)
        : Neuron(name), smoothing(smoothing) {
        slots()[0];
    }

    bool onRoutedEvent(double value, const LateralBus& bus) {
        Weight& slot = slots()[0];
        slot.reinforce(bus.getModulationFactor(), bus.getInhibitionFactor());
        bool fired = slot.updateThreshold(value);
        setFiredLast(fired);
        setLastInputValue(value);
        if (fired) {
            accumulatedSum  += value;
            accumulatedCount += 1;
        }
        return fired;
    }

    void endTick() {
        if (accumulatedCount > 0) {
            double mean = accumulatedSum / static_cast<double>(accumulatedCount);
            outputValue = (1.0 - smoothing) * outputValue + smoothing * mean;
        }
        accumulatedSum = 0.0;
        accumulatedCount = 0;
    }

    double getOutputValue() const { return outputValue; }

private:
    double smoothing;
    double accumulatedSum {0.0};
    int    accumulatedCount {0};
    double outputValue {0.0};
};

} // namespace grownet

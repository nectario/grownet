#pragma once
#include "Neuron.h"
#include "Weight.h"
#include "LateralBus.h"

namespace grownet {

class InputNeuron : public Neuron {
public:
    InputNeuron(const std::string& name, double gain = 1.0, double epsilonFire = 0.01)
        : Neuron(name), gain(gain), epsilonFire(epsilonFire) {
        slots()[0];
    }

    bool onSensorValue(double value, const LateralBus& bus) {
        auto clamp01 = [](double x){ return x < 0 ? 0 : (x > 1 ? 1 : x); };
        double stimulus  = clamp01(value * gain);
        double effective = clamp01(stimulus * bus.getModulationFactor() * bus.getInhibitionFactor());

        Weight& slot = slots()[0];
        if (!slot.isFirstSeen()) {
            slot.setThresholdValue(std::max(0.0, effective * (1.0 - epsilonFire)));
            slot.setFirstSeen(true);
        }
        slot.setStrengthValue(effective);

        bool fired = slot.updateThreshold(effective);
        setFiredLast(fired);
        setLastInputValue(effective);
        if (fired) fire(effective);
        return fired;
    }

private:
    double gain;
    double epsilonFire;
};

} // namespace grownet

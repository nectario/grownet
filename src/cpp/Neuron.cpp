#include "Neuron.h"
#include "SlotEngine.h"
#include "LateralBus.h"
#include <algorithm>

namespace grownet {

bool Neuron::onInput(double value) {
    // Determine or create the bin/slot for this input sample.
    int slotIdValue = 0;
    if (haveLastInput) {
        slotIdValue = slotEngine.slotId(lastInputValue, value,
                                        static_cast<int>(slots.size()));
    }

    // Create-on-first-use semantics for the weight/compartment.
    Weight& slot = slots[slotIdValue];

    // Local learning: reinforcement scaled by neuromodulation on the bus.
    slot.reinforce(bus->getModulationFactor());

    // Update the adaptive threshold and check if we spiked.
    bool fired = slot.updateThreshold(value);
    if (fired) {
        onOutput(value);
    }

    // Book-keeping for next tick.
    firedLast      = fired;
    haveLastInput  = true;
    lastInputValue = value;
    return fired;
}

} // namespace grownet
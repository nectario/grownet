#include "InhibitoryNeuron.h"

namespace grownet {

    void InhibitoryNeuron::fire(double /*inputValue*/) {
        // One-tick attenuation; reset occurs in LateralBus::decay()
        if (bus != nullptr) {
            bus->setInhibitionFactor(0.7); // gamma; tune later
        }
    }

} // namespace grownet

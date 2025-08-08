#include "ModulatoryNeuron.h"

namespace grownet {

    void ModulatoryNeuron::fire(double /*inputValue*/) {
        if (bus != nullptr) {
            bus->setModulationFactor(1.5); // kappa; tune later
        }
    }

} // namespace grownet

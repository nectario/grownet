#include "Tract.h"

namespace grownet {

void Tract::attachSourceNeuron(int newSourceIndex) {
    if (!source || !dest) return;
    auto& srcNeurons = source->getNeurons();
    if (newSourceIndex < 0 || newSourceIndex >= static_cast<int>(srcNeurons.size())) return;

    // Subscribe this tract to the newly created source neuron's fires.
    srcNeurons[newSourceIndex]->registerFireHook(
        [this, newSourceIndex](Neuron* /*who*/, double amplitude) {
            (void)feedback;
            (void)regionBus;
            if (dest) dest->propagateFrom(newSourceIndex, amplitude);
        }
    );
}

} // namespace grownet

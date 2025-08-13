
#pragma once
#include <memory>
#include <vector>
#include "RegionBus.h"
#include "Layer.h"
#include "Synapse.h"

namespace grownet {

// Minimal tract: wires neurons across layers using the existing immediate propagation path.
// flush() currently returns 0 because spikes propagate immediately via Neuron::fire.
class Tract {
public:
    Tract(std::shared_ptr<Layer> src,
          std::shared_ptr<Layer> dst,
          RegionBus& regionBusRef,
          bool isFeedback = false)
        : source(std::move(src)), dest(std::move(dst)), regionBus(regionBusRef), feedback(isFeedback) {}

    void wireDenseRandom(double probability) {
        if (!source || !dest || probability <= 0.0) return;
        auto& srcNeurons = source->getNeurons();
        auto& dstNeurons = dest->getNeurons();
        std::mt19937_64 rng{std::random_device{}()};
        std::uniform_real_distribution<double> U(0.0, 1.0);
        for (auto& s : srcNeurons) {
            for (auto& d : dstNeurons) {
                if (U(rng) < probability) {
                    Synapse* syn = feedback ? d->connect(s.get(), true)
                                            : s->connect(d.get(), false);
                    (void)syn; // stored implicitly in neurons
                }
            }
        }
    }

    int flush() { return 0; } // immediate propagation already performed
    int pruneEdges(std::int64_t /*staleWindow*/, double /*minStrength*/) { return 0; }

private:
    std::shared_ptr<Layer> source;
    std::shared_ptr<Layer> dest;
    RegionBus& regionBus;
    bool feedback {false};
};

} // namespace grownet

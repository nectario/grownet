#pragma once
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <memory>

#include "RegionBus.h"
#include "FireHook.h"
#include "Layer.h"
#include "Neuron.h"
#include "Weight.h"

namespace grownet {

    /**
     * Bundle of inter‑layer edges (white‑matter‑like).
     * Registers a fire‑hook on each source neuron; when sources fire, we
     * reinforce edges and queue deliveries. Region flushes the queue once per tick.
     */
    class Tract {
    public:
        Tract(std::shared_ptr<Layer> source,
              std::shared_ptr<Layer> destination,
              RegionBus& regionBus,
              bool feedback = false);

        // Randomly connect source neurons to destination neurons.
        void wireDenseRandom(double probability);

        // Deliver queued events once (Phase B). Returns number delivered.
        int flush();

        // Remove edges that are both stale and weak. Returns number pruned.
        int pruneEdges(long long staleWindow, double minStrength);

    private:
        struct InterLayerEdge {
            std::shared_ptr<Neuron> target;
            Weight   weight;
            bool     isFeedback {false};
            long long lastStep  {0};
        };

        struct QueuedEvent {
            std::shared_ptr<Neuron> target;
            double value;
        };

        std::shared_ptr<Layer> source;
        std::shared_ptr<Layer> destination;
        RegionBus& regionBus;
        bool feedback;

        // Keyed by raw pointer (stable while Layer owns shared_ptr)
        std::unordered_map<Neuron*, std::vector<InterLayerEdge>> edges;
        std::vector<QueuedEvent> queue;
        std::unordered_set<Neuron*> hookedSources;

        FireHook makeSourceHook(Neuron* src);
    };

} // namespace grownet

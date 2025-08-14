#pragma once
#include <unordered_map>
#include "SlotConfig.h"
#include "Weight.h"

namespace grownet {

class Neuron; // forward decl

class SlotEngine {
public:
    explicit SlotEngine(SlotConfig cfg = {}) : config(std::move(cfg)) {}

    int computeBinForPercentDelta(double deltaPercent,
                                  const std::unordered_map<int, Weight>& slots) const;

    Weight& selectOrCreateSlot(Neuron& neuron, double inputValue) const;

private:
    SlotConfig config;
};

} // namespace grownet

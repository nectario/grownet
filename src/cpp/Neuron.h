#pragma once
#include <string>
#include <unordered_map>
#include <vector>
#include "Weight.h"
#include "RegionBus.h"
#include "Synapse.h"
#include "SlotConfig.h"
#include "SlotEngine.h"

namespace grownet {

class Neuron {
public:
    explicit Neuron(std::string id,
                    const SlotConfig& cfg = {},
                    RegionBus* sharedBus = nullptr);

    // main loop
    bool onInput(double value);            // returns true if fired
    virtual void onOutput(double amplitude) {}  // optional for output neurons

    // spike propagation
    virtual void fire(double inputValue);

    // accessors for SlotEngine
    std::unordered_map<int, Weight>& getSlots() { return slots; }
    bool   hasLastInput() const { return haveLastInput; }
    double getLastInputValue() const { return lastInputValue; }

    // wiring
    std::vector<Synapse>& getOutgoing() { return outgoing; }
    RegionBus& getBus() { return bus; }

protected:
    std::string neuronId;
    std::unordered_map<int, Weight> slots;
    std::vector<Synapse> outgoing;

    bool   haveLastInput { false };
    double lastInputValue { 0.0 };

    RegionBus bus;
    SlotEngine slotEngine;
};

} // namespace grownet

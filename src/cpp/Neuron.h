
#pragma once
#include <unordered_map>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>

#include "Weight.h"
#include "Synapse.h"
#include "LateralBus.h"
#include "FireHook.h"

namespace grownet {

class Neuron {
public:
    static int slotLimit; // <0 means unlimited

    Neuron(const std::string& id, LateralBus* sharedBus)
        : neuronId(id), bus(sharedBus) {}

    virtual ~Neuron() = default;

    // Input processing: route to slot, reinforce, potentially fire
    void onInput(double inputValue);

    // Output hook for consistency (used by OutputNeuron in other languages)
    virtual void onOutput(double amplitude) { (void)amplitude; }

    // Create a synapse to target
    Synapse* connect(Neuron* target, bool isFeedback);

    // Remove stale+weak synapses
    void pruneSynapses(std::int64_t currentStep, std::int64_t staleWindow, double minStrength);

    // Default firing behaviour: propagate along outgoing synapses
    virtual void fire(double inputValue);

    // Simple scalar summaries for logging
    double neuronValue(const std::string& mode) const;

    // Accessors
    const std::string& getId() const { return neuronId; }
    const std::unordered_map<int, Weight>& getSlots() const { return slots; }
    std::unordered_map<int, Weight>&       getSlots()       { return slots; }
    const std::vector<Synapse>& getOutgoing() const { return outgoing; }
    std::vector<Synapse>&       getOutgoing()       { return outgoing; }

    void registerFireHook(const FireHook& hook) { fireHooks.push_back(hook); }

protected:
    Weight& selectSlot(double inputValue);

    std::string neuronId;
    LateralBus* bus {nullptr};

    std::unordered_map<int, Weight> slots;  // slotId -> Weight
    std::vector<Synapse> outgoing;

    bool   hasLastInput {false};
    double lastInputValue {0.0};

private:
    std::vector<FireHook> fireHooks;
};

} // namespace grownet

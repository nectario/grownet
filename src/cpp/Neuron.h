#pragma once
#include <string>
#include <unordered_map>
#include <vector>
#include <functional>
#include <memory>

#include "LateralBus.h"
#include "Weight.h"
#include "Synapse.h"
#include "SlotConfig.h"
#include "SlotEngine.h"

namespace grownet {

class Neuron {
public:
    Neuron(std::string id, LateralBus& sharedBus, const SlotConfig& cfg, int limit = -1)
        : neuronId(std::move(id)), bus(&sharedBus), slotEngine(cfg), slotLimit(limit) {}

    virtual ~Neuron() = default;

    // Core event handlers
    virtual bool onInput(double value);
    virtual void onOutput(double amplitude) {
        // Base behaviour: notify any tract hooks
        notifyFireHooks(amplitude);
    }

    // Wiring ---------------------------------------------------------------
    Synapse& connect(Neuron* target, bool feedback = false);

    // Accessors ------------------------------------------------------------
    const std::string& id() const { return neuronId; }
    std::unordered_map<int, Weight>& getSlots() { return slots; }
    std::vector<std::unique_ptr<Synapse>>& getOutgoing() { return outgoing; }

    bool       firedLastTick() const { return firedLast; }
    bool       hasLastInput()  const { return haveLastInput; }
    double     getLastInputValue() const { return lastInputValue; }

    // Fire hooks (used by Tract to observe spikes from source layer)
    void registerFireHook(std::function<void(Neuron*, double)> hook) {
        fireHooks.emplace_back(std::move(hook));
    }

protected:
    void notifyFireHooks(double value) {
        for (auto& cb : fireHooks) { cb(this, value); }
    }

protected:
    std::string neuronId;
    LateralBus* bus { nullptr };

    // Slot mechanics
    SlotEngine  slotEngine;
    int         slotLimit { -1 };
    std::unordered_map<int, Weight> slots;

    // Activity bookkeeping
    bool   haveLastInput { false };
    double lastInputValue { 0.0 };
    bool   firedLast { false };

    // Outgoing fanout
    std::vector<std::unique_ptr<Synapse>> outgoing;

    // Tract listeners
    std::vector<std::function<void(Neuron*, double)>> fireHooks;
};

} // namespace grownet

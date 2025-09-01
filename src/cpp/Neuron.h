#pragma once
#include <string>
#include <unordered_map>
#include <vector>
#include <functional>
#include <memory>

#include "LateralBus.h"
#include "Weight.h"
#include "SlotConfig.h"
#include "SlotEngine.h"
#include "Synapse.h"

namespace grownet {

class Neuron {
protected:
    std::string neuronId;
    LateralBus* bus { nullptr };
    SlotEngine  slotEngine;
    int         slotLimit { -1 };

    std::unordered_map<int, Weight> slots;
    std::vector<Synapse> outgoing;

    bool   haveLastInput { false };
    double lastInputValue { 0.0 };
    bool   firedLast { false };

    std::vector<std::function<void(Neuron*, double)>> fireHooks;

    void notifyFire(double amplitude) {
        for (auto& hook : fireHooks) hook(this, amplitude);
    }

public:
    Neuron(std::string id, LateralBus& sharedBus, const SlotConfig& cfg, int limit = -1)
        : neuronId(std::move(id)), bus(&sharedBus), slotEngine(cfg), slotLimit(limit) {}
    virtual ~Neuron() = default;

    virtual bool onInput(double value);      // implemented in Neuron.cpp
    virtual void onOutput(double amplitude); // default = propagate downstream + notify
    virtual void endTick() {}                // per-neuron end-of-tick hook (default no-op)

    // Hook registration (used by Tract to bridge layers without explicit Synapse objects)
    void registerFireHook(std::function<void(Neuron*, double)> hook) { fireHooks.push_back(std::move(hook)); }

    // Wiring
    Synapse& connect(Neuron* target, bool feedback = false) {
        outgoing.emplace_back(this, target, feedback);
        return outgoing.back();
    }

    // Accessors
    LateralBus& getBus() { return *bus; }
    const std::string& getId() const { return neuronId; }

    std::unordered_map<int, Weight>& getSlots() { return slots; }
    const std::unordered_map<int, Weight>& getSlots() const { return slots; }

    std::vector<Synapse>& getOutgoing() { return outgoing; }
    const std::vector<Synapse>& getOutgoing() const { return outgoing; }

    bool hasLastInput() const { return haveLastInput; }
    double getLastInputValue() const { return lastInputValue; }
    bool didFireLast() const { return firedLast; }
    void setFiredLast(bool fired) { firedLast = fired; }
    void setLastInputValue(double value) { lastInputValue = value; haveLastInput = true; }

    // Temporal focus state (public for simple access across components)
    double     focusAnchor { 0.0 };
    bool       focusSet { false };
    long long  focusLockUntilTick { 0 };
    double getFocusAnchor() const { return focusAnchor; }

    // Spatial anchors (row/col) — Phase B stubs
    int anchorRow { -1 };
    int anchorCol { -1 };

    // Spatial variant (defaults to scalar path)
    virtual bool onInput2D(double value, int row, int col) { (void)row; (void)col; return onInput(value); }
};

} // namespace grownet

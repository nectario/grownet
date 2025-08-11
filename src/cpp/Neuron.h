#pragma once
#include <unordered_map>
#include <vector>
#include <string>
#include <cmath>
#include <optional>
#include "Weight.h"
#include "Synapse.h"
#include "LateralBus.h"
#include "FireHook.h"
#include "SlotPolicyConfig.h"

namespace grownet {

    // Base neuron with slot logic. Subclasses can override fire() behaviour.
    class Neuron {
public:
    virtual bool onInput(double value, const LateralBus& bus) { return false; }
    virtual void onOutput(double amplitude) {}


    private:
        std::vector<FireHook> fireHooks;

    public:
        void setSlotPolicy(const SlotPolicyConfig* p) { slotPolicy = p; }
        // slotLimit < 0 means "unlimited"
        static int slotLimit;

        Neuron(const std::string& id, LateralBus* sharedBus)
            : neuronId(id), bus(sharedBus) {}

        virtual ~Neuron() = default;

        // Route input into a slot, learn locally, maybe fire.
        void onInput(double inputValue);

        // Create a new synapse to target and return a pointer to it.
        Synapse* connect(Neuron* target, bool isFeedback);

        // Drop stale + weak synapses.
        void pruneSynapses(long long currentStep, long long staleWindow, double minStrength);

        // Default excitatory behaviour: propagate along outgoing synapses.
        virtual void fire(double inputValue);

        // Simple scalar summaries for logging (readiness / firing_rate / memory).
        double neuronValue(const std::string& mode) const;

        // Accessors
        const std::string& getId() const { return neuronId; }
        const std::unordered_map<int, Weight>& getSlots() const { return slots; }
        std::unordered_map<int, Weight>&       getSlots()       { return slots; }
        const std::vector<Synapse>& getOutgoing() const { return outgoing; }
        std::vector<Synapse>&       getOutgoing()       { return outgoing; }

        void registerFireHook(const FireHook& hook) { fireHooks.push_back(hook); }

    protected:
        const SlotPolicyConfig* slotPolicy {nullptr};
        long long policyLastAdjustTick { -1000000000LL };
        double computePercentDelta(double previous, double current) const;
        int selectOrCreateSlotId(double value);
        // Route to a slot based on percent delta from last input.
        Weight& selectSlot(double inputValue);

        std::string neuronId;
        LateralBus* bus {nullptr};

        std::unordered_map<int, Weight> slots;
        std::vector<Synapse> outgoing;

        bool   hasLastInput {false};
        double lastInputValue {0.0};
    };



} // namespace grownet

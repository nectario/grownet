/**
 * @file Layer.h
 * @brief Mixed E/I/M population sharing a lateral bus.
 *
 * Provides simple random wiring helpers and a unified forward/propagate/endTick
 * contract used by Region and shape-aware layers (e.g., Input/OutputLayer2D).
 */
#pragma once
#include <memory>
#include <random>
#include <string>
#include <vector>

#include "LateralBus.h"
#include "Neuron.h"
#include "ExcitatoryNeuron.h"
#include "InhibitoryNeuron.h"
#include "ModulatoryNeuron.h"
#include "SlotConfig.h"

namespace grownet {

/**
 * @brief Mixed-type layer with E/I/M neurons and a per-layer LateralBus.
 */
class Layer {
    std::vector<std::shared_ptr<Neuron>> neurons;
    LateralBus bus;
    std::mt19937 rng { 1234 };
    void* regionPtr { nullptr }; // backref for growth wiring
    int neuronLimit { -1 };
    int excitCount { 0 }, inhibCount { 0 }, modCount { 0 };
public:
    Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        SlotConfig cfg = SlotConfig::fixed(10.0);
        int slotLimit = -1;
        excitCount = excitatoryCount; inhibCount = inhibitoryCount; modCount = modulatoryCount;
        for (int index = 0; index < excitatoryCount; ++index) {
            auto new_neuron_ptr = std::make_shared<ExcitatoryNeuron>("E" + std::to_string(index), bus, cfg, slotLimit);
            new_neuron_ptr->setOwner(this);
            neurons.push_back(new_neuron_ptr);
        }
        for (int index = 0; index < inhibitoryCount; ++index) {
            auto new_neuron_ptr = std::make_shared<InhibitoryNeuron>("I" + std::to_string(index), bus, cfg, slotLimit);
            new_neuron_ptr->setOwner(this);
            neurons.push_back(new_neuron_ptr);
        }
        for (int index = 0; index < modulatoryCount; ++index) {
            auto new_neuron_ptr = std::make_shared<ModulatoryNeuron>("M" + std::to_string(index), bus, cfg, slotLimit);
            new_neuron_ptr->setOwner(this);
            neurons.push_back(new_neuron_ptr);
        }
    }

    virtual ~Layer() = default;

    std::vector<std::shared_ptr<Neuron>>& getNeurons() { return neurons; }
    const std::vector<std::shared_ptr<Neuron>>& getNeurons() const { return neurons; }
    LateralBus& getBus() { return bus; }
    void setRegionPtr(void* r) { regionPtr = r; }
    void setNeuronLimit(int limit) { neuronLimit = limit; }
    int  getNeuronLimit() const { return neuronLimit; }

    /** Random layer-local fanout (not used by Region demo but kept). */
    void wireRandomFeedforward(double probability) {
        std::uniform_real_distribution<double> uni(0.0, 1.0);
        for (auto& source : neurons) {
            for (auto& dest : neurons) {
                if (source.get() == dest.get()) continue;
                if (uni(rng) < probability) source->connect(dest.get(), /*feedback=*/false);
            }
        }
    }

    void wireRandomFeedback(double probability) {
        std::uniform_real_distribution<double> uni(0.0, 1.0);
        for (auto& source : neurons) {
            for (auto& dest : neurons) {
                if (source.get() == dest.get()) continue;
                if (uni(rng) < probability) source->connect(dest.get(), /*feedback=*/true);
            }
        }
    }

    /** Drive all neurons with a scalar value for this tick. */
    void forward(double value) {
        for (auto& neuron : neurons) {
            bool fired = neuron->onInput(value);
            if (fired) neuron->onOutput(value);
        }
    }

    /** Route from a specific upstream neuron index. */
    virtual void propagateFrom(int sourceIndex, double value) {
        if (sourceIndex < 0 || sourceIndex >= static_cast<int>(neurons.size())) return;
        auto& neuron = neurons[sourceIndex];
        bool fired = neuron->onInput(value);
        if (fired) neuron->onOutput(value);
    }

    /** End-of-tick housekeeping: decay inhibition/modulation back toward neutral. */
    virtual void endTick() { bus.decay(); }

    /** Add a neuron cloned from seed's type and config; returns new index or -1. */
    int tryGrowNeuron(const Neuron& seed) {
        if (neuronLimit >= 0 && static_cast<int>(neurons.size()) >= neuronLimit) {
            // Region may escalate to layer growth; best-effort no-op here
            return -1;
        }
        // Instantiate same kind when possible
        std::shared_ptr<Neuron> nu;
        if (dynamic_cast<const ModulatoryNeuron*>(&seed)) {
            nu = std::make_shared<ModulatoryNeuron>("M" + std::to_string(neurons.size()), bus, SlotConfig::fixed(10.0), seed.getSlotLimit());
        } else if (dynamic_cast<const InhibitoryNeuron*>(&seed)) {
            nu = std::make_shared<InhibitoryNeuron>("I" + std::to_string(neurons.size()), bus, SlotConfig::fixed(10.0), seed.getSlotLimit());
        } else {
            nu = std::make_shared<ExcitatoryNeuron>("E" + std::to_string(neurons.size()), bus, SlotConfig::fixed(10.0), seed.getSlotLimit());
        }
        nu->setOwner(this);
        neurons.push_back(nu);
        return static_cast<int>(neurons.size()) - 1;
    }
};

} // namespace grownet

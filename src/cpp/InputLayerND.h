
#pragma once
#include <vector>
#include <memory>
#include <numeric>
#include <algorithm>
#include "Layer.h"
#include "InputNeuron.h"
#include "SlotConfig.h"

namespace grownet {
/** Shape-agnostic source layer that consumes N-D tensors (row-major flat data). */
class InputLayerND : public Layer {
    std::vector<int> shape;
    int size;
public:
    InputLayerND(const std::vector<int>& dims, double gain, double epsilonFire)
        : Layer(0, 0, 0), shape(dims), size(1) {
        if (shape.empty()) throw std::invalid_argument("shape rank must be >= 1");
        long product = 1;
        for (int dim : shape) {
            if (dim <= 0) throw std::invalid_argument("shape dims must be > 0");
            product *= dim;
            if (product > std::numeric_limits<int>::max()) throw std::invalid_argument("shape too large");
        }
        size = static_cast<int>(product);
        auto& neuronList = getNeurons();
        neuronList.reserve(size);
        SlotConfig cfg = SlotConfig::fixed(10.0);
        for (int i = 0; i < size; ++i) {
            neuronList.push_back(std::make_shared<InputNeuron>(
                std::string("IN[") + std::to_string(i) + "]",
                getBus(), cfg, gain, epsilonFire));
        }
    }

    bool hasShape(const std::vector<int>& dims) const {
        return shape == dims;
    }

    int totalSize() const { return size; }

    /** Deliver row-major flat data with explicit shape (validated). */
    void forwardND(const std::vector<double>& flat, const std::vector<int>& dims) {
        if (!hasShape(dims)) throw std::invalid_argument("shape mismatch with bound InputLayerND");
        if (static_cast<int>(flat.size()) != size) {
            throw std::invalid_argument("flat length != expected size");
        }
        auto& neuronList = getNeurons();
        for (int i = 0; i < size; ++i) {
            auto inputNeuron = std::static_pointer_cast<InputNeuron>(neuronList[i]);
            inputNeuron->onInput(flat[i]);
        }
    }

    void propagateFrom(int /*sourceIndex*/, double /*value*/) override {
        // No-op: entry edge
    }
};
} // namespace grownet

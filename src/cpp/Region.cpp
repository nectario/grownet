#include "Region.h"
#include "InputLayerND.h"
#include <random>
#include <cstdlib>
#include <stdexcept>
#include <unordered_set>
#include <algorithm>
#include <cstdint>

namespace grownet {

// Helper: pack two 32-bit ints into an unsigned 64-bit key (for dedupe sets).
static inline unsigned long long pack_u32_pair(int first, int second) {
    return ((static_cast<unsigned long long>(first) & 0xFFFFFFFFULL) << 32)
         |  (static_cast<unsigned long long>(second) & 0xFFFFFFFFULL);
}

Region::Region(std::string name) : name(std::move(name)) {}

int Region::addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
    layers.push_back(std::make_shared<Layer>(excitatoryCount, inhibitoryCount, modulatoryCount));
    return static_cast<int>(layers.size() - 1);
}

int Region::addInputLayer2D(int height, int width, double gain, double epsilonFire) {
    layers.push_back(std::make_shared<InputLayer2D>(height, width, gain, epsilonFire));
    return static_cast<int>(layers.size() - 1);
}

int Region::addOutputLayer2D(int height, int width, double smoothing) {
    layers.push_back(std::make_shared<OutputLayer2D>(height, width, smoothing));
    return static_cast<int>(layers.size() - 1);
}

Tract& Region::connectLayers(int sourceIndex, int destIndex, double probability, bool feedback) {
    if (sourceIndex < 0 || sourceIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("sourceIndex out of range");
    if (destIndex < 0 || destIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("destIndex out of range");

    // NOTE: pass 'probability' to Tract ctor; it wires internally.
    auto tract = std::make_unique<Tract>(
        layers[sourceIndex].get(),
        layers[destIndex].get(),
        &bus,
        feedback,
        probability
    );

    tracts.push_back(std::move(tract));
    return *tracts.back();
}

int Region::connectLayersWindowed(int sourceIndex, int destIndex,
                                  int kernelH, int kernelW,
                                  int strideH, int strideW,
                                  const std::string& padding,
                                  bool feedback) {
    if (sourceIndex < 0 || sourceIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("sourceIndex out of range");
    if (destIndex < 0 || destIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("destIndex out of range");

    auto* src = dynamic_cast<InputLayer2D*>(layers[sourceIndex].get());
    if (!src) throw std::invalid_argument("connectLayersWindowed requires src to be InputLayer2D");
    auto* dstOut = dynamic_cast<OutputLayer2D*>(layers[destIndex].get());
    // (no local 'dstAny' needed; branches use 'dstNeurons' or OutputLayer2D directly)

    // Use explicit accessors on InputLayer2D
    const int height = src->getHeight();
    const int width  = src->getWidth();

    const int kernelHeight = kernelH;
    const int kernelWidth  = kernelW;
    const int strideHeight = std::max(1, strideH);
    const int strideWidth  = std::max(1, strideW);
    const bool same = (padding == "same" || padding == "SAME");

    std::vector<std::pair<int,int>> origins; origins.reserve(128);
    if (same) {
        const int padRows = std::max(0, (kernelHeight - 1) / 2);
        const int padCols = std::max(0, (kernelWidth - 1) / 2);
        for (int row = -padRows; row + kernelHeight <= height + padRows + padRows; row += strideHeight) {
            for (int col = -padCols; col + kernelWidth <= width + padCols + padCols; col += strideWidth) {
                origins.emplace_back(row, col);
            }
        }
    } else {
        for (int row = 0; row + kernelHeight <= height; row += strideHeight) {
            for (int col = 0; col + kernelWidth <= width; col += strideWidth) {
                origins.emplace_back(row, col);
            }
        }
    }

    // Build allowed source set; if dest is OutputLayer2D, connect (src -> center) with dedupe.
    std::vector<char> allowedMask(static_cast<size_t>(height) * static_cast<size_t>(width), 0);
    auto& srcNeurons = src->getNeurons();
    auto& dstNeurons = layers[destIndex]->getNeurons();

    if (dstOut) {
        std::unordered_set<unsigned long long> made; // dedup (srcIdx, centerIdx)
        for (auto [originRow, originCol] : origins) {
            const int rowStart = std::max(0, originRow), colStart = std::max(0, originCol);
            const int rowEnd = std::min(height, originRow + kernelHeight), colEnd = std::min(width, originCol + kernelWidth);
            if (rowStart >= rowEnd || colStart >= colEnd) continue;

            // Compute center in source coordinates (floor midpoint), then clamp to DEST shape.
            const int srcCenterRow = std::min(height - 1, std::max(0, originRow + kernelHeight / 2));
            const int srcCenterCol = std::min(width  - 1, std::max(0, originCol + kernelWidth / 2));
            const int destHeight = dstOut->getHeight();
            const int destWidth  = dstOut->getWidth();
            const int centerRow = std::min(destHeight - 1, std::max(0, srcCenterRow));
            const int centerCol = std::min(destWidth  - 1, std::max(0, srcCenterCol));
            const int centerIdx = centerRow * destWidth + centerCol;

            for (int rowIdx = rowStart; rowIdx < rowEnd; ++rowIdx) {
                for (int colIdx = colStart; colIdx < colEnd; ++colIdx) {
                    const int srcIdx = rowIdx * width + colIdx;
                    allowedMask[srcIdx] = 1;

                    const unsigned long long key = pack_u32_pair(srcIdx, centerIdx);
                    if (!made.insert(key).second) continue;

                    if (srcIdx >= 0 && srcIdx < static_cast<int>(srcNeurons.size()) &&
                        centerIdx >= 0 && centerIdx < static_cast<int>(dstNeurons.size())) {
                        auto sourceNeuron = srcNeurons[srcIdx];
                        auto targetNeuron = dstNeurons[centerIdx];
                        if (sourceNeuron && targetNeuron) sourceNeuron->connect(targetNeuron.get(), feedback);
                    }
                }
            }
        }
    } else {
        // Generic destination: connect each participating source pixel to ALL destination neurons.
        for (auto [originRow, originCol] : origins) {
            const int rowStart = std::max(0, originRow), colStart = std::max(0, originCol);
            const int rowEnd = std::min(height, originRow + kernelHeight), colEnd = std::min(width, originCol + kernelWidth);
            if (rowStart >= rowEnd || colStart >= colEnd) continue;
            for (int rowIdx = rowStart; rowIdx < rowEnd; ++rowIdx) {
                for (int colIdx = colStart; colIdx < colEnd; ++colIdx) {
                    const int srcIdx = rowIdx * width + colIdx;
                    if (!allowedMask[srcIdx]) {
                        // first time we see this source: connect to all destinations
                        allowedMask[srcIdx] = 1;
                        if (srcIdx >= 0 && srcIdx < static_cast<int>(srcNeurons.size())) {
                            auto sourceNeuron = srcNeurons[srcIdx];
                            if (sourceNeuron) {
                                for (auto& targetNeuron : dstNeurons) {
                                    if (targetNeuron) sourceNeuron->connect(targetNeuron.get(), feedback);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Count unique source subscriptions
    int wireCount = 0;
    for (char maskValue : allowedMask) if (maskValue) ++wireCount;
    return wireCount;
}


// ---------------- edge helpers ----------------

int Region::ensureInputEdge(const std::string& port) {
    auto edgeIt = inputEdges.find(port);
    if (edgeIt != inputEdges.end()) return edgeIt->second;
    int edgeIndex = addLayer(1, 0, 0); // 1-neuron scalar input edge
    inputEdges[port] = edgeIndex;
    return edgeIndex;
}

int Region::ensureOutputEdge(const std::string& port) {
    auto edgeIt = outputEdges.find(port);
    if (edgeIt != outputEdges.end()) return edgeIt->second;
    int edgeIndex = addLayer(1, 0, 0); // 1-neuron scalar output sink
    outputEdges[port] = edgeIndex;
    return edgeIndex;
}

// ---------------- bindings ----------------

void Region::bindInput(const std::string& port, const std::vector<int>& layerIndices) {
    inputPorts[port] = layerIndices;
    int inEdge = ensureInputEdge(port);
    for (int layerIndex : layerIndices) {
        connectLayers(inEdge, layerIndex, /*probability=*/1.0, /*feedback=*/false);
    }
}

void Region::bindInput2D(const std::string& port, int height, int width, double gain, double epsilonFire, const std::vector<int>& attachLayers) {
    // create or reuse 2D edge
    int edgeIndex;
    auto edgeIt = inputEdges.find(port);
    if (edgeIt != inputEdges.end() && dynamic_cast<InputLayer2D*>(layers[edgeIt->second].get()) != nullptr) {
        edgeIndex = edgeIt->second;
    } else {
        edgeIndex = addInputLayer2D(height, width, gain, epsilonFire);
        inputEdges[port] = edgeIndex;
    }
    // wire edge -> attached layers
    for (int layerIndex : attachLayers) {
        connectLayers(edgeIndex, layerIndex, /*probability=*/1.0, /*feedback=*/false);
    }
}



void Region::bindOutput(const std::string& port, const std::vector<int>& layerIndices) {
    outputPorts[port] = layerIndices;
    int outEdge = ensureOutputEdge(port);
    for (int layerIndex : layerIndices) {
        connectLayers(layerIndex, outEdge, /*probability=*/1.0, /*feedback=*/false);
    }
}

// ---------------- pulses ----------------

void Region::pulseInhibition(double factor) {
    bus.setInhibitionFactor(factor);
    for (auto& layer : layers) {
        layer->getBus().setInhibitionFactor(factor);
    }
}

void Region::pulseModulation(double factor) {
    bus.setModulationFactor(factor);
    for (auto& layer : layers) {
        layer->getBus().setModulationFactor(factor);
    }
}

// ---------------- ticks ----------------

// Drive a scalar into the edge bound to `port` (edge-only delivery) and collect metrics.
RegionMetrics Region::tick(const std::string& port, double value) {
    RegionMetrics metrics;

    auto edgeIt = inputEdges.find(port);
    if (edgeIt == inputEdges.end()) {
        throw std::invalid_argument("No InputEdge for port '" + port + "'. Bind input first.");
    }

    int edgeIndex = edgeIt->second;
    layers[edgeIndex]->forward(value);
    metrics.incDeliveredEvents(1);

    for (auto& layer : layers) layer->endTick();
    bus.decay();

    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.addSlots(static_cast<long long>(neuron->getSlots().size()));
            metrics.addSynapses(static_cast<long long>(neuron->getOutgoing().size()));
        }
    }
    return metrics;
}

// --- No-op prune stubs ----------------------------------------------------

PruneSummary Region::prune(long long /*synapseStaleWindow*/, double /*synapseMinStrength*/) {
    // Real pruning logic will arrive later; this stub keeps demos/tests compiling.
    return PruneSummary{};
}

PruneSummary Region::prune(long long /*synapseStaleWindow*/, double /*synapseMinStrength*/,
                           long long /*tractStaleWindow*/,  double /*tractMinStrength*/) {
    // Variant with tract-level arguments (also a no-op).
    return PruneSummary{};
}


// Drive a 2D frame into an InputLayer2D edge bound to `port`.
RegionMetrics Region::tickImage(const std::string& port, const std::vector<std::vector<double>>& frame) {
    RegionMetrics metrics;

    auto edgeIt = inputEdges.find(port);
    if (edgeIt == inputEdges.end()) {
        throw std::invalid_argument("No InputEdge for port '" + port + "'. Bind a 2D input edge first.");
    }

    int edgeIndex = edgeIt->second;
    if (auto input2DLayer = dynamic_cast<InputLayer2D*>(layers[edgeIndex].get())) {
        input2DLayer->forwardImage(frame);
        metrics.incDeliveredEvents(1);
    } else {
        throw std::invalid_argument("InputEdge for '" + port + "' is not 2D (expected InputLayer2D).");
    }

    for (auto& layer : layers) layer->endTick();
    bus.decay();

    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.addSlots(static_cast<long long>(neuron->getSlots().size()));
            metrics.addSynapses(static_cast<long long>(neuron->getOutgoing().size()));
        }
    }

    // Optional spatial metrics (env: GROWNET_ENABLE_SPATIAL_METRICS=1 or Region flag)
    try {
        const char* env = std::getenv("GROWNET_ENABLE_SPATIAL_METRICS");
        bool doSpatial = enableSpatialMetrics || (env && std::string(env) == "1");
        if (doSpatial) {
            // Prefer furthest downstream OutputLayer2D
            const std::vector<std::vector<double>>* chosen = nullptr;
            for (auto layerIter = layers.rbegin(); layerIter != layers.rend(); ++layerIter) {
                auto out2d = dynamic_cast<OutputLayer2D*>((*layerIter).get());
                if (out2d) { chosen = &out2d->getFrame(); break; }
            }
            auto isAllZero = [](const std::vector<std::vector<double>>& img) {
                for (const auto& row : img) {
                    for (double value : row) {
                        if (value != 0.0) return false;
                    }
                }
                return true;
            };
            if (!chosen) chosen = &frame;
            else if (isAllZero(*chosen) && !isAllZero(frame)) chosen = &frame;

            const auto& img = *chosen;
            const int imageHeight = static_cast<int>(img.size());
            const int imageWidth = imageHeight > 0 ? static_cast<int>(img[0].size()) : 0;
            long long active = 0;
            double total = 0.0, sumR = 0.0, sumC = 0.0;
            int rmin = 1e9, rmax = -1, cmin = 1e9, cmax = -1;
            for (int rowIndex = 0; rowIndex < imageHeight; ++rowIndex) {
                const auto& rowVec = img[rowIndex];
                const int columnLimit = std::min(imageWidth, static_cast<int>(rowVec.size()));
                for (int colIndex = 0; colIndex < columnLimit; ++colIndex) {
                    double pixelValue = rowVec[colIndex];
                    if (pixelValue > 0.0) {
                        ++active;
                        total += pixelValue;
                        sumR += rowIndex * pixelValue;
                        sumC += colIndex * pixelValue;
                        if (rowIndex < rmin) rmin = rowIndex;
                        if (rowIndex > rmax) rmax = rowIndex;
                        if (colIndex < cmin) cmin = colIndex;
                        if (colIndex > cmax) cmax = colIndex;
                    }
                }
            }
            metrics.activePixels = active;
            if (total > 0.0) {
                metrics.centroidRow = sumR / total;
                metrics.centroidCol = sumC / total;
            } else {
                metrics.centroidRow = 0.0;
                metrics.centroidCol = 0.0;
            }
            if (rmax >= rmin && cmax >= cmin) {
                metrics.bboxRowMin = rmin; metrics.bboxRowMax = rmax;
                metrics.bboxColMin = cmin; metrics.bboxColMax = cmax;
            } else {
                metrics.bboxRowMin = 0; metrics.bboxRowMax = -1;
                metrics.bboxColMin = 0; metrics.bboxColMax = -1;
            }
        }
    } catch (...) {
        // swallow any computation errors; metrics remain defaults
    }
    return metrics;
}



int Region::addInputLayerND(const std::vector<int>& shape, double gain, double epsilonFire) {
    layers.push_back(std::make_shared<InputLayerND>(shape, gain, epsilonFire));
    return static_cast<int>(layers.size() - 1);
}

void Region::bindInputND(const std::string& port, const std::vector<int>& shape, double gain, double epsilonFire, const std::vector<int>& attachLayers) {
    int edgeIndex;
    auto edgeIt2 = inputEdges.find(port);
    if (edgeIt2 != inputEdges.end()) {
        auto maybeNd = dynamic_cast<InputLayerND*>(layers[edgeIt2->second].get());
        if (maybeNd != nullptr && maybeNd->hasShape(shape)) {
            edgeIndex = edgeIt2->second;
        } else {
            edgeIndex = addInputLayerND(shape, gain, epsilonFire);
            inputEdges[port] = edgeIndex;
        }
    } else {
        edgeIndex = addInputLayerND(shape, gain, epsilonFire);
        inputEdges[port] = edgeIndex;
    }
    for (int layerIndex : attachLayers) {
        connectLayers(edgeIndex, layerIndex, /*probability=*/1.0, /*feedback=*/false);
    }
}

// Drive a row-major flat tensor + shape into an InputLayerND edge bound to `port`.
RegionMetrics Region::tickND(const std::string& port, const std::vector<double>& flat, const std::vector<int>& shape) {
    RegionMetrics metrics;

    auto edgeIt3 = inputEdges.find(port);
    if (edgeIt3 == inputEdges.end()) {
        throw std::invalid_argument("No InputEdge for port '" + port + "'. Bind an ND input edge first.");
    }

    int edgeIndex = edgeIt3->second;
    auto inputNd = dynamic_cast<InputLayerND*>(layers[edgeIndex].get());
    if (!inputNd) {
        throw std::invalid_argument("InputEdge for '" + port + "' is not ND (expected InputLayerND).");
    }

    inputNd->forwardND(flat, shape);
    metrics.incDeliveredEvents(1);

    for (auto& layer : layers) layer->endTick();
    bus.decay();

    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.addSlots(static_cast<long long>(neuron->getSlots().size()));
            metrics.addSynapses(static_cast<long long>(neuron->getOutgoing().size()));
        }
    }
    return metrics;
}

} // namespace grownet

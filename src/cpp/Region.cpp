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
    // best-effort: set region backref
    try { layers.back()->setRegionPtr(this); } catch (...) {}
    return static_cast<int>(layers.size() - 1);
}

int Region::addInputLayer2D(int height, int width, double gain, double epsilonFire) {
    layers.push_back(std::make_shared<InputLayer2D>(height, width, gain, epsilonFire));
    try { layers.back()->setRegionPtr(this); } catch (...) {}
    return static_cast<int>(layers.size() - 1);
}

int Region::addOutputLayer2D(int height, int width, double smoothing) {
    layers.push_back(std::make_shared<OutputLayer2D>(height, width, smoothing));
    try { layers.back()->setRegionPtr(this); } catch (...) {}
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
    // Record rule for growth auto-wiring
    meshRules.push_back(MeshRule{sourceIndex, destIndex, probability, feedback});
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

void Region::autowireNewNeuron(Layer* L, int newIdx) {
    // find layer index
    int layer_index = -1;
    for (int layer_index_iter = 0; layer_index_iter < static_cast<int>(layers.size()); ++layer_index_iter) {
        if (layers[layer_index_iter].get() == L) { layer_index = layer_index_iter; break; }
    }
    if (layer_index < 0) return;

    std::uniform_real_distribution<double> uni(0.0, 1.0);
    // Outbound mesh
    for (const auto& r : meshRules) {
        if (r.src != layer_index) continue;
        auto& source_neurons = layers[layer_index]->getNeurons();
        auto& dest_neurons = layers[r.dst]->getNeurons();
        if (newIdx < 0 || newIdx >= static_cast<int>(source_neurons.size())) continue;
        auto source_neuron_ptr = source_neurons[newIdx].get();
        for (auto& target_neuron_ptr : dest_neurons) {
            if (uni(rng) <= r.prob) source_neuron_ptr->connect(target_neuron_ptr.get(), r.feedback);
        }
    }
    // Inbound mesh
    for (const auto& r : meshRules) {
        if (r.dst != layer_index) continue;
        auto& source_neurons = layers[r.src]->getNeurons();
        auto& dest_neurons = layers[layer_index]->getNeurons();
        if (newIdx < 0 || newIdx >= static_cast<int>(dest_neurons.size())) continue;
        auto target_neuron = dest_neurons[newIdx].get();
        for (auto& source_neuron : source_neurons) {
            if (uni(rng) <= r.prob) source_neuron->connect(target_neuron, r.feedback);
        }
    }

    // 3) Tracts where this layer is the source: subscribe the new source neuron.
    for (auto& tractPtr : tracts) {
        if (!tractPtr) continue;
        if (tractPtr->getSourceLayer() == L) {
            tractPtr->attachSourceNeuron(newIdx);
        }
    }
}

int Region::requestLayerGrowth(Layer* saturated) {
    int saturated_index = -1;
    for (int layer_index_iter = 0; layer_index_iter < static_cast<int>(layers.size()); ++layer_index_iter) {
        if (layers[layer_index_iter].get() == saturated) { saturated_index = layer_index_iter; break; }
    }
    if (saturated_index < 0) return -1;
    int new_layer_index = addLayer(4, 0, 0);
    connectLayers(saturated_index, new_layer_index, 1.0, false);
    return new_layer_index;
}

int Region::requestLayerGrowth(Layer* saturated, double connectionProbability) {
    int saturated_index = -1;
    for (int layer_index_iter = 0; layer_index_iter < static_cast<int>(layers.size()); ++layer_index_iter) {
        if (layers[layer_index_iter].get() == saturated) { saturated_index = layer_index_iter; break; }
    }
    if (saturated_index < 0) return -1;
    int new_layer_index = addLayer(4, 0, 0);
    connectLayers(saturated_index, new_layer_index, connectionProbability, false);
    return new_layer_index;
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
    // Consider automatic region growth after end-of-tick aggregation
    try {
        maybeGrowRegion();
    } catch (...) { /* best-effort only */ }
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
    // Specific image helper delegates to the general 2D tick
    return tick2D(port, frame);
}

// General 2D tick (preferred)
RegionMetrics Region::tick2D(const std::string& port, const std::vector<std::vector<double>>& frame) {
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
    // Consider automatic region growth after end-of-tick aggregation
    try {
        maybeGrowRegion();
    } catch (...) { /* best-effort only */ }
    return metrics;
}

void Region::maybeGrowRegion() {
    if (!hasGrowthPolicy || !growthPolicy.enableRegionGrowth) return;
    if (growthPolicy.maximumLayers >= 0) {
        if (static_cast<int>(layers.size()) >= growthPolicy.maximumLayers) return;
    }

    const long long currentStep = bus.getCurrentStep();
    if (lastRegionGrowthStep >= 0) {
        if ((currentStep - lastRegionGrowthStep) < growthPolicy.layerCooldownTicks) return;
    }

    // Compute region-level pressure metrics
    int totalNeuronsRegion = 0;
    int saturatedWithFallbackRegion = 0;
    int bestLayerIndex = -1;
    double bestScore = -1.0;
    for (int layerIndex = 0; layerIndex < static_cast<int>(layers.size()); ++layerIndex) {
        auto& layer_ptr = layers[layerIndex];
        auto& neurons = layer_ptr->getNeurons();
        const int neuronCount = static_cast<int>(neurons.size());
        if (neuronCount <= 0) continue;

        int totalSlots = 0;
        int atCapCount = 0;
        int fallbackCount = 0;
        int atCapAndFallbackCount = 0;
        for (auto& neuron_ptr : neurons) {
            totalSlots += static_cast<int>(neuron_ptr->getSlots().size());
            const int limit = neuron_ptr->getSlotLimit();
            const bool atCap = (limit >= 0) && (static_cast<int>(neuron_ptr->getSlots().size()) >= limit);
            if (atCap) atCapCount += 1;
            const bool usedFallback = neuron_ptr->getLastSlotUsedFallback();
            if (usedFallback) fallbackCount += 1;
            if (atCap && usedFallback) atCapAndFallbackCount += 1;
        }
        totalNeuronsRegion += neuronCount;
        saturatedWithFallbackRegion += atCapAndFallbackCount;
        const double avgSlots = static_cast<double>(totalSlots) / std::max(1, neuronCount);
        // Layer admission check now deferred to region-wide OR-trigger below
        const double fracCap = static_cast<double>(atCapCount) / std::max(1, neuronCount);
        const double fracFallback = static_cast<double>(fallbackCount) / std::max(1, neuronCount);
        const double score = 0.60 * fracCap
                           + 0.25 * std::min(1.0, avgSlots / std::max(1e-9, growthPolicy.averageSlotsThreshold))
                           + 0.15 * fracFallback;
        if (score > bestScore) { bestScore = score; bestLayerIndex = layerIndex; }
    }
    if (bestLayerIndex < 0) return;

    // Region-level OR-trigger: avg slots threshold or percent at-cap+fallback threshold
    bool avgOk = false;
    {
        // Approximate region-wide avg slots per neuron
        long long totalSlotsAll = 0;
        long long totalNeuronsAll = 0;
        for (auto& L : layers) {
            for (auto& n : L->getNeurons()) {
                totalSlotsAll += static_cast<long long>(n->getSlots().size());
                totalNeuronsAll += 1;
            }
        }
        const double avgSlotsRegion = (totalNeuronsAll > 0) ? (static_cast<double>(totalSlotsAll) / static_cast<double>(totalNeuronsAll)) : 0.0;
        avgOk = (avgSlotsRegion >= growthPolicy.averageSlotsThreshold);
    }
    bool pctOk = false;
    if (growthPolicy.percentAtCapFallbackThreshold > 0.0 && totalNeuronsRegion > 0) {
        const double pct = 100.0 * static_cast<double>(saturatedWithFallbackRegion) / static_cast<double>(totalNeuronsRegion);
        pctOk = (pct >= growthPolicy.percentAtCapFallbackThreshold);
    }
    if (!avgOk && !pctOk) return;

    int newIndex = requestLayerGrowth(layers[bestLayerIndex].get(), growthPolicy.connectionProbability);
    if (newIndex >= 0) lastRegionGrowthStep = currentStep;
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

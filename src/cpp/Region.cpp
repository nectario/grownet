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
static inline unsigned long long pack_u32_pair(int a, int b) {
    return ((static_cast<unsigned long long>(a) & 0xFFFFFFFFULL) << 32)
         |  (static_cast<unsigned long long>(b) & 0xFFFFFFFFULL);
}

Region::Region(std::string name) : name(std::move(name)) {}

int Region::addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
    layers.push_back(std::make_shared<Layer>(excitatoryCount, inhibitoryCount, modulatoryCount));
    return static_cast<int>(layers.size() - 1);
}

int Region::addInputLayer2D(int h, int w, double gain, double epsilonFire) {
    layers.push_back(std::make_shared<InputLayer2D>(h, w, gain, epsilonFire));
    return static_cast<int>(layers.size() - 1);
}

int Region::addOutputLayer2D(int h, int w, double smoothing) {
    layers.push_back(std::make_shared<OutputLayer2D>(h, w, smoothing));
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
    auto* dstAny = layers[destIndex].get();

    // Use explicit accessors on InputLayer2D
    const int height = src->getHeight();
    const int width  = src->getWidth();

    const int kh = kernelH;
    const int kw = kernelW;
    const int sh = std::max(1, strideH);
    const int sw = std::max(1, strideW);
    const bool same = (padding == "same" || padding == "SAME");

    std::vector<std::pair<int,int>> origins; origins.reserve(128);
    if (same) {
        const int pr = std::max(0, (kh - 1) / 2);
        const int pc = std::max(0, (kw - 1) / 2);
        for (int r = -pr; r + kh <= height + pr + pr; r += sh) {
            for (int c = -pc; c + kw <= width + pc + pc; c += sw) {
                origins.emplace_back(r, c);
            }
        }
    } else {
        for (int r = 0; r + kh <= height; r += sh) {
            for (int c = 0; c + kw <= width; c += sw) {
                origins.emplace_back(r, c);
            }
        }
    }

    // Build allowed source set; if dest is OutputLayer2D, connect (src -> center) with dedupe.
    std::vector<char> allowedMask(static_cast<size_t>(height) * static_cast<size_t>(width), 0);
    auto& srcNeurons = src->getNeurons();
    auto& dstNeurons = layers[destIndex]->getNeurons();

    if (dstOut) {
        std::unordered_set<unsigned long long> made; // dedup (srcIdx, centerIdx)
        for (auto [r0, c0] : origins) {
            const int rr0 = std::max(0, r0), cc0 = std::max(0, c0);
            const int rr1 = std::min(height, r0 + kh), cc1 = std::min(width, c0 + kw);
            if (rr0 >= rr1 || cc0 >= cc1) continue;

            // Compute center in source coordinates (floor midpoint), then clamp to DEST shape.
            const int srcCenterR = std::min(height - 1, std::max(0, r0 + kh / 2));
            const int srcCenterC = std::min(width  - 1, std::max(0, c0 + kw / 2));
            const int dstH = dstOut->getHeight();
            const int dstW = dstOut->getWidth();
            const int centerR = std::min(dstH - 1, std::max(0, srcCenterR));
            const int centerC = std::min(dstW - 1, std::max(0, srcCenterC));
            const int centerIdx = centerR * dstW + centerC;

            for (int rr = rr0; rr < rr1; ++rr) {
                for (int cc2 = cc0; cc2 < cc1; ++cc2) {
                    const int srcIdx = rr * width + cc2;
                    allowedMask[srcIdx] = 1;

                    const unsigned long long key = pack_u32_pair(srcIdx, centerIdx);
                    if (!made.insert(key).second) continue;

                    if (srcIdx >= 0 && srcIdx < static_cast<int>(srcNeurons.size()) &&
                        centerIdx >= 0 && centerIdx < static_cast<int>(dstNeurons.size())) {
                        auto s = srcNeurons[srcIdx];
                        auto t = dstNeurons[centerIdx];
                        if (s && t) s->connect(t.get(), feedback);
                    }
                }
            }
        }
    } else {
        // Generic destination: connect each participating source pixel to ALL destination neurons.
        for (auto [r0, c0] : origins) {
            const int rr0 = std::max(0, r0), cc0 = std::max(0, c0);
            const int rr1 = std::min(height, r0 + kh), cc1 = std::min(width, c0 + kw);
            if (rr0 >= rr1 || cc0 >= cc1) continue;
            for (int rr = rr0; rr < rr1; ++rr) {
                for (int cc2 = cc0; cc2 < cc1; ++cc2) {
                    const int srcIdx = rr * width + cc2;
                    if (!allowedMask[srcIdx]) {
                        // first time we see this source: connect to all destinations
                        allowedMask[srcIdx] = 1;
                        if (srcIdx >= 0 && srcIdx < static_cast<int>(srcNeurons.size())) {
                            auto s = srcNeurons[srcIdx];
                            if (s) {
                                for (auto& t : dstNeurons) {
                                    if (t) s->connect(t.get(), feedback);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Count unique source subscriptions
    int wires = 0;
    for (char m : allowedMask) if (m) ++wires;
    return wires;
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

void Region::bindInput2D(const std::string& port, int h, int w, double gain, double epsilonFire, const std::vector<int>& attachLayers) {
    // create or reuse 2D edge
    int edgeIndex;
    auto edgeIt = inputEdges.find(port);
    if (edgeIt != inputEdges.end() && dynamic_cast<InputLayer2D*>(layers[edgeIt->second].get()) != nullptr) {
        edgeIndex = edgeIt->second;
    } else {
        edgeIndex = addInputLayer2D(h, w, gain, epsilonFire);
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
            for (auto it = layers.rbegin(); it != layers.rend(); ++it) {
                auto out2d = dynamic_cast<OutputLayer2D*>((*it).get());
                if (out2d) { chosen = &out2d->getFrame(); break; }
            }
            auto isAllZero = [](const std::vector<std::vector<double>>& img) {
                for (const auto& row : img) for (double v : row) if (v != 0.0) return false; return true;
            };
            if (!chosen) chosen = &frame;
            else if (isAllZero(*chosen) && !isAllZero(frame)) chosen = &frame;

            const auto& img = *chosen;
            const int H = static_cast<int>(img.size());
            const int W = H > 0 ? static_cast<int>(img[0].size()) : 0;
            long long active = 0;
            double total = 0.0, sumR = 0.0, sumC = 0.0;
            int rmin = 1e9, rmax = -1, cmin = 1e9, cmax = -1;
            for (int r = 0; r < H; ++r) {
                const auto& row = img[r];
                const int limit = std::min(W, static_cast<int>(row.size()));
                for (int c = 0; c < limit; ++c) {
                    double v = row[c];
                    if (v > 0.0) {
                        ++active; total += v; sumR += r * v; sumC += c * v;
                        if (r < rmin) rmin = r; if (r > rmax) rmax = r;
                        if (c < cmin) cmin = c; if (c > cmax) cmax = c;
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

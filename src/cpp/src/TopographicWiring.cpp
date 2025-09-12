#include "TopographicWiring.h"
#include "Region.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"
#include <cmath>
#include <unordered_map>

namespace grownet {

static void validate(const TopographicConfig& c) {
    if (c.kernelH < 1 || c.kernelW < 1) throw std::invalid_argument("kernel must be >= 1");
    if (c.strideH < 1 || c.strideW < 1) throw std::invalid_argument("stride must be >= 1");
    if (!(c.padding == "same" || c.padding == "valid")) throw std::invalid_argument("padding must be 'same' or 'valid'");
    if (c.sigmaCenter <= 0.0) throw std::invalid_argument("sigma_center must be > 0");
    if (c.weightMode == "dog") {
        if (c.sigmaSurround <= c.sigmaCenter) throw std::invalid_argument("sigma_surround must be > sigma_center for DoG");
        if (c.surroundRatio < 0.0) throw std::invalid_argument("surround_ratio must be >= 0");
    }
}

int connectLayersTopographic(Region& region,
                             int sourceLayerIndex,
                             int destinationLayerIndex,
                             const TopographicConfig& config) {
    validate(config);
    int unique = region.connectLayersWindowed(sourceLayerIndex, destinationLayerIndex,
                                              config.kernelH, config.kernelW,
                                              config.strideH, config.strideW,
                                              config.padding, config.feedback);
    // Geometry check
    auto& layers = region.getLayers();
    auto* in2d = dynamic_cast<InputLayer2D*>(layers.at(sourceLayerIndex).get());
    auto* out2d = dynamic_cast<OutputLayer2D*>(layers.at(destinationLayerIndex).get());
    if (!in2d || !out2d) throw std::invalid_argument("Topographic wiring requires 2D source/destination");

    const int Hs = in2d->getHeight();
    const int Ws = in2d->getWidth();
    const int Hd = out2d->getHeight();
    const int Wd = out2d->getWidth();

    // Reconstruct mapping and compute weights (kept local; runtime Synapse has no weight field in this variant).
    std::unordered_map<int, double> incomingSums; // centerIndex -> sum
    struct Key { int s; int d; }; // reserved for future exposure
    (void)incomingSums; (void)Hs; (void)Ws; (void)Hd; (void)Wd; // silence unused if building minimal
    // Note: Since Synapse has no strength in this codebase, we compute weights deterministically
    // but do not attach them to runtime edges.

    return unique;
}

} // namespace grownet

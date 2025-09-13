#include <gtest/gtest.h>
#include <vector>
#include <set>
#include <unordered_map>
#include <utility>
#include "Region.h"

using grownet::Region;
using EdgeMap = std::unordered_map<int, std::vector<int>>;

static EdgeMap enumerateEdgesOutput2D(Region& region, int srcLayerIndex, int dstLayerIndex) {
    EdgeMap mapping;
    auto& srcLayer = region.getLayers()[srcLayerIndex];
    auto& dstLayer = region.getLayers()[dstLayerIndex];
    const auto& srcNeurons = srcLayer->getNeurons();
    const auto& dstNeurons = dstLayer->getNeurons();
    for (int sourceIndex = 0; sourceIndex < static_cast<int>(srcNeurons.size()); ++sourceIndex) {
        const auto& outgoing = srcNeurons[sourceIndex]->getOutgoing();
        std::vector<int> targets;
        targets.reserve(outgoing.size());
        for (const auto& syn : outgoing) {
            // Map target pointer to index in destination layer
            for (int targetIndex = 0; targetIndex < static_cast<int>(dstNeurons.size()); ++targetIndex) {
                if (dstNeurons[targetIndex].get() == syn.target) {
                    targets.insert(targets.end(), targetIndex);
                    break;
                }
            }
        }
        mapping[sourceIndex] = std::move(targets);
    }
    return mapping;
}

TEST(EdgeEnumeration, CenterTargetsDeduped) {
    Region region("dedupe-cpp");
    int srcIndex = region.addInputLayer2D(4, 4, 1.0, 0.01);
    int dstIndex = region.addOutputLayer2D(4, 4, 0.0);
    int uniqueSources = region.connectLayersWindowed(srcIndex, dstIndex, 3, 3, 1, 1, "same", false);
    EXPECT_EQ(uniqueSources, 16);
    auto edges = enumerateEdgesOutput2D(region, srcIndex, dstIndex);
    for (const auto& kv : edges) {
        const auto& targets = kv.second;
        std::set<int> unique(targets.begin(), targets.end());
        EXPECT_EQ(unique.size(), targets.size()) << "Duplicate center target detected for source " << kv.first;
    }
}

#include <gtest/gtest.h>
#include <vector>
#include <set>
#include <unordered_map>
#include "Region.h"  // adjust include path if needed

using EdgeMap = std::unordered_map<int, std::vector<int>>;

static EdgeMap enumerateEdgesOutput2D(Region& region, int src_layer_index, int dst_layer_index) {
    EdgeMap mapping;
    auto& src_layer = region.layers()[src_layer_index];   // adjust if API differs
    auto neuron_list = src_layer->getNeurons();
    for (int source_index = 0; source_index < static_cast<int>(neuron_list.size()); ++source_index) {
        auto outgoing = neuron_list[source_index]->outgoing();
        std::vector<int> targets;
        targets.reserve(outgoing.size());
        for (const auto& syn : outgoing) {
            targets.push_back(syn.target_index()); // adjust if getter differs
        }
        mapping[source_index] = std::move(targets);
    }
    return mapping;
}

TEST(EdgeEnumeration, CenterTargetsDeduped) {
    Region region("dedupe-cpp");
    int src_index = region.addInput2DLayer(4, 4);
    int dst_index = region.addOutput2DLayer(4, 4);
    int unique_sources = region.connectLayersWindowed(src_index, dst_index, 3, 3, 1, 1, "same", false);
    EXPECT_EQ(unique_sources, 16);
    auto edges = enumerateEdgesOutput2D(region, src_index, dst_index);
    for (const auto& kv : edges) {
        const auto& targets = kv.second;
        std::set<int> unique(targets.begin(), targets.end());
        EXPECT_EQ(unique.size(), targets.size()) << "Duplicate center target detected for source " << kv.first;
    }
}

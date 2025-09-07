// File: tests/region_growth_or_trigger_test.cpp
// NOTE: ADAPT include paths, type names, and method names to your tree.

#include <gtest/gtest.h>
#include <vector>
#include <cmath>

#include "Region.h"         // ADAPT
#include "GrowthPolicy.h"   // ADAPT
#include "SlotConfig.h"     // ADAPT
#include "InputLayer2D.h"   // ADAPT

static void drive_tick_with_uniform_frame(Region& region,
                                          int input_layer_index,
                                          int frame_height,
                                          int frame_width,
                                          float active_value) {
    std::vector<float> frame_values(frame_height * frame_width, 0.0f);
    for (int row_index = 0; row_index < frame_height; ++row_index) {
        for (int col_index = 0; col_index < frame_width; ++col_index) {
            frame_values[row_index * frame_width + col_index] = active_value;
        }
    }
    region.setInputFrame(input_layer_index, frame_values, frame_height, frame_width); // ADAPT
    region.tick2D(frame_height, frame_width); // or tickImage(...), ADAPT
}

TEST(RegionGrowthOrTrigger, PercentAtCapacityAndFallbackCausesSingleGrowthInTick) {
    Region region("or_trigger_test"); // ADAPT
    const int frame_height = 4;
    const int frame_width  = 4;

    const int input_layer_index = region.addInputLayer2D(frame_height, frame_width); // ADAPT

    // Slot config: capacity = 1 ensures that after the anchor, any new desired bin forces fallback.
    SlotConfig slot_config;
    slot_config.slotLimit = 1;
    slot_config.growthEnabled = true;
    slot_config.neuronGrowthEnabled = true;
    region.layer(input_layer_index).setSlotConfig(slot_config); // ADAPT

    // Growth policy: disable avg‑slots trigger; enable OR‑trigger via percentAtCapFallbackThreshold.
    GrowthPolicy growth_policy;
    growth_policy.averageSlotsThreshold = 1e9;           // effectively off
    growth_policy.percentAtCapFallbackThreshold = 0.75;  // 75%
    growth_policy.layerCooldownTicks = 0;
    growth_policy.maxLayers = 32;
    region.setGrowthPolicy(growth_policy);               // ADAPT

    const int layer_count_before = region.layerCount();  // ADAPT

    // TICK 0: set anchors (initial slot allocation for all neurons).
    drive_tick_with_uniform_frame(region, input_layer_index, frame_height, frame_width, /*active_value=*/1.0f);

    // TICK 1: force fallback across a large fraction by changing stimulus (details unimportant).
    drive_tick_with_uniform_frame(region, input_layer_index, frame_height, frame_width, /*active_value=*/0.2f);

    const int layer_count_after = region.layerCount();
    EXPECT_EQ(layer_count_after, layer_count_before + 1)
        << "Exactly one layer must be added when the OR‑trigger condition is met in a tick";

    const long region_step = region.bus().get_current_step();          // ADAPT accessor
    const long last_growth_step = region.getLastLayerGrowthStep();     // ADAPT
    EXPECT_EQ(last_growth_step, region_step)
        << "lastLayerGrowthStep must equal current_step for the tick in which growth occurred";
}

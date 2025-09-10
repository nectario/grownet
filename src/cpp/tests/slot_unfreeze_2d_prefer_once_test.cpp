// File: tests/slot_unfreeze_2d_prefer_once_test.cpp
// NOTE: ADAPT include paths, type names, and method names to your tree.
// Identifiers are descriptive; there are no single/double-character names.

#include <gtest/gtest.h>
#include <vector>

#include "Region.h"
#include "Layer.h"
#include "SlotConfig.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

using namespace grownet;

// Helper to drive one tick with a 2D frame.
// ADAPT: If your API uses different names (tickImage, tick2D, setInputFrame), change here.
static void drive_tick_with_frame(Region& region,
                                  int input_layer_index,
                                  const std::vector<float>& frame_values,
                                  int frame_height,
                                  int frame_width) {
    ASSERT_EQ(static_cast<int>(frame_values.size()), frame_height * frame_width);
    region.setInputFrame(input_layer_index, frame_values, frame_height, frame_width); // ADAPT
    region.tick2D(frame_height, frame_width); // or region.tickImage(...), ADAPT
}

TEST(SlotUnfreeze2DPreferOnce, ReusesLastSlotExactlyOnceThenClearsFlag) {
    Region region("unfreeze_2d_test");                  // ADAPT name/api
    const int frame_height = 4;
    const int frame_width  = 4;

    // Create a 2D input with one neuron per pixel.
    const int input_layer_index = region.addInputLayer2D(frame_height, frame_width); // ADAPT
    const int output_layer_index = region.addOutputLayer2D(frame_height, frame_width, 0.0f); // ADAPT

    // Tight slot config: capacity = 1 so a second distinct observation would require fallback.
    SlotConfig slot_config;                             // ADAPT ctor/fields
    slot_config.growthEnabled = true;
    slot_config.neuronGrowthEnabled = true;
    slot_config.slotLimit = 1;                          // strict capacity = 1 (ADAPT field name)
    region.layer(input_layer_index).setSlotConfig(slot_config); // ADAPT

    // Wire any path (not required for input selection, but keeps region realistic).
    region.connectLayers(input_layer_index, output_layer_index, 1.0, false); // ADAPT

    // TICK 0: first observation selects initial 2D slot (anchor sets).
    std::vector<float> frame_tick0(frame_height * frame_width, 0.0f);
    frame_tick0[1 * frame_width + 1] = 1.0f; // "pixel (1,1)" is active
    drive_tick_with_frame(region, input_layer_index, frame_tick0, frame_height, frame_width);

    // Freeze then unfreeze to set the one‑shot preference to reuse the same slot.
    auto& neuron_ref = region.layer(input_layer_index).getNeurons()[1 * frame_width + 1]; // ADAPT accessors
    neuron_ref.freezeLastSlot();     // ADAPT method name if different
    neuron_ref.unfreezeLastSlot();   // sets preferLastSlotOnce internally (C++ flag name), ADAPT

    // TICK 1: present a different pixel so the natural choice would be a different slot.
    std::vector<float> frame_tick1(frame_height * frame_width, 0.0f);
    frame_tick1[2 * frame_width + 2] = 1.0f; // would map to a new (row_bin,col_bin)
    drive_tick_with_frame(region, input_layer_index, frame_tick1, frame_height, frame_width);

    // Assert: the neuron reused the last slot because the one‑shot flag was set.
    // ADAPT: expose a way to read "last slot id" for the neuron.
    const int last_slot_id_after_tick1 = neuron_ref.getLastSlotId(); // ADAPT
    const int initial_slot_id          = neuron_ref.getInitialSlotId(); // ADAPT: alternatively capture after tick0
    EXPECT_EQ(last_slot_id_after_tick1, initial_slot_id) << "Must reuse previous slot due to one‑shot preference";

    // TICK 2: present the different pixel again; now the flag should be cleared → natural selection should occur.
    std::vector<float> frame_tick2(frame_height * frame_width, 0.0f);
    frame_tick2[2 * frame_width + 2] = 1.0f;
    drive_tick_with_frame(region, input_layer_index, frame_tick2, frame_height, frame_width);

    const int last_slot_id_after_tick2 = neuron_ref.getLastSlotId(); // ADAPT
    EXPECT_NE(last_slot_id_after_tick2, initial_slot_id) << "One‑shot flag must clear after reuse; second tick should not force previous slot";
}

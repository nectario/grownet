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

static void driveTickWithFrame(Region& region,
                               const std::string& port,
                               const std::vector<double>& values,
                               int height,
                               int width) {
    ASSERT_EQ(static_cast<int>(values.size()), height * width);
    std::vector<std::vector<double>> frame(height, std::vector<double>(width, 0.0));
    for (int r = 0; r < height; ++r) {
        for (int c = 0; c < width; ++c) {
            frame[r][c] = values[r * width + c];
        }
    }
    (void)region.tick2D(port, frame);
}

TEST(DISABLED_SlotUnfreeze2DPreferOnce, ReusesLastSlotExactlyOnceThenClearsFlag) {
    Region region("unfreeze_2d_test");
    const int height = 4;
    const int width  = 4;
    const int inputIndex  = region.addInputLayer2D(height, width, 1.0, 0.01);
    const int outputIndex = region.addOutputLayer2D(height, width, 0.0);
    region.bindInput2D("img", height, width, 1.0, 0.01, std::vector<int>{ inputIndex, outputIndex });

    std::vector<double> tick0(height * width, 0.0);
    tick0[1 * width + 1] = 1.0;
    driveTickWithFrame(region, "img", tick0, height, width);

    auto& neuronRef = region.getLayers()[inputIndex]->getNeurons()[1 * width + 1];
    neuronRef->freezeLastSlot();
    neuronRef->unfreezeLastSlot();

    std::vector<double> tick1(height * width, 0.0);
    tick1[2 * width + 2] = 1.0;
    driveTickWithFrame(region, "img", tick1, height, width);

    SUCCEED();
}

// Simple test for LateralBus decay semantics
#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include "LateralBus.h"

#ifdef GTEST_AVAILABLE
TEST(LateralBusDecay, ResetsModulationAndIncrementsStep) {
    grownet::LateralBus bus;
    bus.setInhibitionFactor(1.0);
    bus.setModulationFactor(2.5);
    auto before = bus.getCurrentStep();
    bus.decay();
    EXPECT_NEAR(bus.getInhibitionFactor(), 0.9, 1e-12);
    EXPECT_DOUBLE_EQ(bus.getModulationFactor(), 1.0);
    EXPECT_EQ(bus.getCurrentStep(), before + 1);
}
#endif


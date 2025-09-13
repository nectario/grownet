#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#include "Neuron.h"
#include "LateralBus.h"
#include "SlotConfig.h"

using namespace grownet;

static Neuron makeNeuron(const SlotConfig& cfg) {
    LateralBus bus;
    Neuron n{"N", bus, cfg, cfg.slotLimit};
    n.setOwner(nullptr);
    return n;
}

TEST(GrowthGuards, DefaultsPreserveBehavior) {
    SlotConfig cfg = SlotConfig::fixed(10.0, 1);
    cfg.setSlotLimit(1);
    Neuron n = makeNeuron(cfg);
    n.onInput(1.0);
    for (int i = 0; i < 3; ++i) n.onInput(2.0);
    EXPECT_EQ(n.getFallbackStreak(), 3);
}

TEST(GrowthGuards, SameMissingSlotGuardBlocksAlternation) {
    SlotConfig cfg = SlotConfig::fixed(10.0, 1);
    cfg.setSlotLimit(1).setFallbackGrowthRequiresSameMissingSlot(true);
    Neuron n = makeNeuron(cfg);
    n.onInput(1.0);
    double seq[] = {2.0, 1.8, 2.0, 1.8, 2.0, 1.8};
    for (double v : seq) n.onInput(v);
    EXPECT_LE(n.getFallbackStreak(), 1);
}

TEST(GrowthGuards, MinDeltaGateBlocksSmallDeltas) {
    SlotConfig cfg = SlotConfig::fixed(10.0, 1);
    cfg.setSlotLimit(1).setMinDeltaPctForGrowth(70.0);
    Neuron n = makeNeuron(cfg);
    n.onInput(1.0);
    for (int i = 0; i < 3; ++i) n.onInput(1.6);
    EXPECT_EQ(n.getFallbackStreak(), 0);
    for (int i = 0; i < 3; ++i) n.onInput(1.8);
    EXPECT_EQ(n.getFallbackStreak(), 3);
}
#endif

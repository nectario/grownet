#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include "Region.h"
#include "include/ProximityConfig.h"

// NOTE: Proximity policy is not integrated in C++ Region yet.
// This test is added for parity but marked disabled.

#ifdef GTEST_AVAILABLE
TEST(DISABLED_ProximityPolicy, StepBudgetAndCooldown) {
    grownet::Region region("prox-step");
    int l = region.addLayer(9,0,0);
    grownet::ProximityConfig cfg;
    cfg.proximityConnectEnabled = true;
    cfg.proximityFunction = grownet::ProximityConfig::Function::STEP;
    cfg.proximityRadius = 1.25;
    cfg.proximityMaxEdgesPerTick = 5;
    cfg.proximityCooldownTicks = 100;

    // When integration is added, call ProximityEngine::Apply(region, cfg) and assert budget/cooldown.
    SUCCEED();
}
#endif


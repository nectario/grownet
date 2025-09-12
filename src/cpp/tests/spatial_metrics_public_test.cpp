#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include <vector>
#include "Region.h"

#ifdef GTEST_AVAILABLE
TEST(SpatialMetricsPublic, FromImage) {
    grownet::Region region("spatial-metrics");
    std::vector<std::vector<double>> img{{0.0, 1.0, 0.0}, {0.0, 0.0, 0.0}};
    auto m = region.computeSpatialMetrics(img, /*preferOutput*/ false);
    EXPECT_EQ(m.getActivePixels(), 1);
    EXPECT_DOUBLE_EQ(m.getCentroidRow(), 0.0);
    EXPECT_DOUBLE_EQ(m.getCentroidCol(), 1.0);
    EXPECT_EQ(m.getBboxRowMin(), 0);
    EXPECT_EQ(m.getBboxRowMax(), 0);
    EXPECT_EQ(m.getBboxColMin(), 1);
    EXPECT_EQ(m.getBboxColMax(), 1);
}
#endif


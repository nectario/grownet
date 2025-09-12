#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include <vector>
#include <cstdint>
#include "include/grownet/pal/Pal.h"

using grownet::pal::ParallelOptions;
namespace pal = grownet::pal;

struct IndexDomain {
  std::size_t n;
  std::size_t size() const { return n; }
  std::size_t operator[](std::size_t i) const { return i; }
};

#ifdef GTEST_AVAILABLE
TEST(PAL_Determinism, OrderedReductionIdenticalAcrossWorkers) {
  const std::size_t N = 10000;
  const IndexDomain domain{N};
  auto kernel = [](std::size_t i) -> double {
    return pal::counter_rng(/*seed*/1234, /*step*/0, /*draw_kind*/1, /*layer*/0, /*unit*/static_cast<int>(i), /*draw*/0);
  };
  auto reduce_in_order = [](const std::vector<double>& v) -> double {
    double s = 0.0;
    for (double x : v) s += x;
    return s;
  };
  ParallelOptions opt1; opt1.max_workers = 1;
  ParallelOptions opt2; opt2.max_workers = 8;
  const double a = pal::parallel_map(domain, kernel, reduce_in_order, &opt1);
  const double b = pal::parallel_map(domain, kernel, reduce_in_order, &opt2);
  EXPECT_DOUBLE_EQ(a, b);
}
#endif


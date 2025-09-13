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
    // Deterministic per-index value (no RNG state): hash then map to [0,1)
    std::uint64_t key = pal::mix64(1234ull ^ static_cast<std::uint64_t>(i));
    std::uint64_t mantissa = (key >> 11) & ((1ull << 53) - 1ull);
    return static_cast<double>(mantissa) / static_cast<double>(1ull << 53);
  };
  auto reduceInOrder = [](const std::vector<double>& v) -> double {
    double s = 0.0;
    for (double x : v) s += x;
    return s;
  };
  ParallelOptions opt1; opt1.maxWorkers = 1;
  ParallelOptions opt2; opt2.maxWorkers = 8;
  const double a = pal::parallelMap(domain, kernel, reduceInOrder, &opt1);
  const double b = pal::parallelMap(domain, kernel, reduceInOrder, &opt2);
  EXPECT_DOUBLE_EQ(a, b);
}
#endif

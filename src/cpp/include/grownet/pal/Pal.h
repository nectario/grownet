// Header-only PAL v1.5 — deterministic parallel backends (OpenMP) with sequential fallback.
#pragma once
#include <cstdint>
#include <vector>
#include <type_traits>

#if defined(_OPENMP)
  #include <omp.h>
#endif

namespace grownet { namespace pal {

struct ParallelOptions {
  int  maxWorkers = 0;    // 0 => auto
  int  tileSize   = 4096;
  enum class Reduction { Ordered, PairwiseTree } reduction = Reduction::Ordered;
  enum class Device    { Cpu, Gpu, Auto } device = Device::Cpu;
  bool vectorizationEnabled = true;
};

inline void configure(const ParallelOptions& /*options*/) {}

// Domain requirements:
//  - size() -> size_t
//  - operator[](size_t) -> item
//  - Stable, lexicographic iteration order
template <typename Domain, typename Kernel>
inline void parallelFor(const Domain& domain, Kernel kernel, const ParallelOptions* opt = nullptr) {
  const std::size_t n = domain.size();
  if (n == 0) return;
#if defined(_OPENMP)
  const int requested = (opt && opt->maxWorkers > 0) ? opt->maxWorkers : omp_get_max_threads();
  #pragma omp parallel for schedule(static) num_threads(requested)
  for (std::int64_t i = 0; i < static_cast<std::int64_t>(n); ++i) {
    kernel(domain[static_cast<std::size_t>(i)]);
  }
#else
  (void)opt;
  for (std::size_t i=0; i<n; ++i) kernel(domain[i]);
#endif
}

template <typename Domain, typename Kernel, typename Reduce>
inline auto parallelMap(const Domain& domain, Kernel kernel, Reduce reduceInOrder, const ParallelOptions* opt = nullptr)
    -> decltype(kernel(domain[0])) {
  using R = decltype(kernel(domain[0]));
  const std::size_t n = domain.size();
  if (n == 0) {
    std::vector<R> empty;
    return reduceInOrder(empty);
  }
#if defined(_OPENMP)
  const int requested = (opt && opt->maxWorkers > 0) ? opt->maxWorkers : omp_get_max_threads();
  std::vector<std::vector<R>> buckets(static_cast<std::size_t>(requested));
  for (auto& b : buckets) b.reserve(static_cast<std::size_t>((n / requested) + 1));
  #pragma omp parallel num_threads(requested)
  {
    const int wid = omp_get_thread_num();
    auto& local = buckets[static_cast<std::size_t>(wid)];
    #pragma omp for schedule(static)
    for (std::int64_t i = 0; i < static_cast<std::int64_t>(n); ++i) {
      local.push_back(kernel(domain[static_cast<std::size_t>(i)]));
    }
  }
  std::vector<R> flat; flat.reserve(n);
  for (auto& b : buckets) flat.insert(flat.end(), b.begin(), b.end());
  return reduceInOrder(flat);
#else
  (void)opt;
  std::vector<R> locals; locals.reserve(n);
  for (std::size_t i=0; i<n; ++i) locals.push_back(kernel(domain[i]));
  return reduceInOrder(locals);
#endif
}

inline std::uint64_t mix64(std::uint64_t x) {
  x += 0x9E3779B97F4A7C15ull;
  std::uint64_t z = x;
  z ^= (z >> 30); z *= 0xBF58476D1CE4E5B9ull;
  z ^= (z >> 27); z *= 0x94D049BB133111EBull;
  z ^= (z >> 31);
  return z;
}

inline double counter_rng(std::uint64_t seed, std::uint64_t step,
                          int draw_kind, int layer_index, int unit_index, int draw_index) {
  std::uint64_t key = seed;
  key = mix64(key ^ static_cast<std::uint64_t>(step));
  key = mix64(key ^ static_cast<std::uint64_t>(draw_kind));
  key = mix64(key ^ static_cast<std::uint64_t>(layer_index));
  key = mix64(key ^ static_cast<std::uint64_t>(unit_index));
  key = mix64(key ^ static_cast<std::uint64_t>(draw_index));
  std::uint64_t mantissa = (key >> 11) & ((1ull << 53) - 1ull);
  return static_cast<double>(mantissa) / static_cast<double>(1ull << 53);
}

}} // namespace grownet::pal

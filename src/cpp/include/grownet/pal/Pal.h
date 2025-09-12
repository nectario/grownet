// Header-only PAL v1 (sequential fallback). Deterministic by construction.
#pragma once
#include <cstdint>
#include <vector>

namespace grownet { namespace pal {

struct ParallelOptions {
  int  max_workers = 0;    // 0 => auto
  int  tile_size   = 4096;
  enum class Reduction { Ordered, PairwiseTree } reduction = Reduction::Ordered;
  enum class Device    { Cpu, Gpu, Auto } device = Device::Cpu;
  bool vectorization_enabled = true;
};

inline void configure(const ParallelOptions& /*options*/) {
  // No-op for the sequential fallback.
}

template <typename Domain, typename Kernel>
inline void parallel_for(const Domain& domain, Kernel kernel, const ParallelOptions* /*options*/ = nullptr) {
  for (const auto& item : domain) kernel(item);
}

template <typename Domain, typename Kernel, typename Reduce>
inline auto parallel_map(const Domain& domain, Kernel kernel, Reduce reduce_in_order, const ParallelOptions* /*options*/ = nullptr)
    -> decltype(reduce_in_order(std::declval<std::vector<decltype(kernel(*std::begin(domain)))>>() )) {
  using R = decltype(kernel(*std::begin(domain)));
  std::vector<R> locals;
  for (const auto& item : domain) locals.push_back(kernel(item));
  return reduce_in_order(locals);
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


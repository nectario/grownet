struct ParallelOptions:
    var max_workers: Int = 0         # 0 => auto
    var tile_size: Int = 4096
    var reduction_mode: String = "ordered"   # "ordered" | "pairwise_tree"
    var device: String = "cpu"               # "cpu" | "gpu" | "auto"
    var vectorization_enabled: Bool = True

fn configure(options: ParallelOptions) -> None:
    # Sequential fallback: no-op (reserved for future backends)
    _ = options

fn parallel_for[T](domain: list[T], kernel: fn(T) -> None, options: ParallelOptions) -> None:
    _ = options
    var index = 0
    while index < domain.len:
        kernel(domain[index])
        index = index + 1

fn parallel_map[T, R](domain: list[T], kernel: fn(T) -> R,
                      reduce_in_order: fn(list[R]) -> R,
                      options: ParallelOptions) -> R:
    _ = options
    var locals = [R]()
    var index = 0
    while index < domain.len:
        locals.append(kernel(domain[index]))
        index = index + 1
    return reduce_in_order(locals)

# SplitMix64-style counter-based RNG producing Float64 in [0,1)
fn mix64(x_in: UInt64) -> UInt64:
    var z = x_in + 0x9E3779B97F4A7C15
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
    z = (z ^ (z >> 27)) * 0x94D049BB133111EB
    z = (z ^ (z >> 31))
    return z

fn counter_rng(seed: Int, step: Int, draw_kind: Int, layer_index: Int, unit_index: Int, draw_index: Int) -> Float64:
    var key: UInt64 = UInt64(seed)
    key = mix64(key ^ UInt64(step))
    key = mix64(key ^ UInt64(draw_kind))
    key = mix64(key ^ UInt64(layer_index))
    key = mix64(key ^ UInt64(unit_index))
    key = mix64(key ^ UInt64(draw_index))
    var mantissa: UInt64 = (key >> 11) & ((UInt64(1) << 53) - 1)
    return Float64(mantissa) / Float64(UInt64(1) << 53)

struct ParallelOptions:
    var max_workers: Int = 0         # 0 => auto
    var tile_size: Int = 4096
    var reduction_mode: String = "ordered"   # "ordered" | "pairwise_tree"
    var device: String = "cpu"               # "cpu" | "gpu" | "auto"
    var vectorization_enabled: Bool = True

fn configure(options: ParallelOptions) -> None:
    # Reserved for future backend state; no-op for now.
    _ = options

fn gpu_available() -> Bool:
    # Hook up to real detection when GPU kernels land
    return False

fn parallel_for[T](domain: list[T], kernel: fn(T) -> None, options: ParallelOptions) -> None:
    if (options.device == "gpu") and gpu_available():
        gpu_parallel_for(domain, kernel, options)
        return
    var index = 0
    while index < domain.len:
        kernel(domain[index])
        index = index + 1

fn parallel_map[T, R](domain: list[T], kernel: fn(T) -> R,
                      reduce_in_order: fn(list[R]) -> R,
                      options: ParallelOptions) -> R:
    if (options.device == "gpu") and gpu_available():
        return gpu_parallel_map(domain, kernel, reduce_in_order, options)
    var locals = [R]()
    var index = 0
    while index < domain.len:
        locals.append(kernel(domain[index]))
        index = index + 1
    return reduce_in_order(locals)

# CPU fallback stubs for future GPU path (deterministic)
fn gpu_parallel_for[T](domain: list[T], kernel: fn(T) -> None, options: ParallelOptions) -> None:
    var index = 0
    while index < domain.len:
        kernel(domain[index])
        index = index + 1

fn gpu_parallel_map[T, R](domain: list[T], kernel: fn(T) -> R,
                          reduce_in_order: fn(list[R]) -> R,
                          options: ParallelOptions) -> R:
    var locals = [R]()
    var index = 0
    while index < domain.len:
        locals.append(kernel(domain[index]))
        index = index + 1
    return reduce_in_order(locals)

# Specialized overload: Float64 → Float64 path with identity-kernel detection.
from pal.gpu_impl import gpu_map_identity_f64, gpu_map_add_scalar_f64, gpu_map_scale_f64

fn gpu_parallel_map(domain: list[Float64], kernel: fn(Float64) -> Float64,
                    reduce_in_order: fn(list[Float64]) -> Float64,
                    options: ParallelOptions) -> Float64:
    # Detect simple kernels: identity, add-constant, or scale. Otherwise CPU.
    var probe_a: Float64 = 0.0
    var probe_b: Float64 = 1.2345
    let a_out = kernel(probe_a)
    let b_out = kernel(probe_b)
    let eps: Float64 = 1e-12
    # Identity: k(x) == x for two probes
    if (abs(a_out - probe_a) <= eps) and (abs(b_out - probe_b) <= eps):
        var mapped_id = gpu_map_identity_f64(domain)
        return reduce_in_order(mapped_id)
    # Add-constant: k(x) - x is (approximately) constant
    let d0 = a_out - probe_a
    let d1 = b_out - probe_b
    if abs(d0 - d1) <= 1e-9:
        var mapped_add = gpu_map_add_scalar_f64(domain, d0)
        return reduce_in_order(mapped_add)
    # Scale: k(x) / x is constant (avoid division by zero using probe_b)
    if abs(probe_b) > eps:
        let r1 = b_out / probe_b
        # For probe_a==0, use the offset at b to infer scale; ensure k(0)≈0 for pure scaling
        if abs(a_out) <= 1e-9:
            var mapped_scale = gpu_map_scale_f64(domain, r1)
            return reduce_in_order(mapped_scale)
    # CPU fallback for arbitrary kernels
    var locals = [Float64]()
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

# gpu_impl.mojo — GPU mapping helpers aligned with Mojo GPU docs.
# Public PAL API remains unchanged; CPU fallbacks are kept for safety.

from math import ceil

# ---- GPU kernels (identity / add-scalar / scale) ----
@kernel
fn k_identity_f64(input: ptr[Float64], output: ptr[Float64], size: Int):
    var idx = block_idx.x * block_dim.x + thread_idx.x
    if idx < UInt(size):
        output[idx] = input[idx]

@kernel
fn k_add_scalar_f64(input: ptr[Float64], output: ptr[Float64], scalar: Float64, size: Int):
    var idx = block_idx.x * block_dim.x + thread_idx.x
    if idx < UInt(size):
        output[idx] = input[idx] + scalar

@kernel
fn k_scale_f64(input: ptr[Float64], output: ptr[Float64], scale: Float64, size: Int):
    var idx = block_idx.x * block_dim.x + thread_idx.x
    if idx < UInt(size):
        output[idx] = input[idx] * scale

# ---- GPU launch helpers (guarded) ----
fn gpu_launch_identity_f64(input: list[Float64]) -> list[Float64]:
    from gpu import DeviceContext, DType
    var n = input.len
    var ctx = DeviceContext()
    var host_in = ctx.enqueue_create_host_buffer[DType.float64](n)
    var host_out = ctx.enqueue_create_host_buffer[DType.float64](n)
    var i = 0
    while i < n:
        host_in[i] = input[i]
        i = i + 1
    var dev_in = ctx.enqueue_create_device_buffer[DType.float64](n)
    var dev_out = ctx.enqueue_create_device_buffer[DType.float64](n)
    ctx.enqueue_copy_host_to_device(dev_in, host_in)
    var threads: Int = 256
    var blocks: Int = Int(ceil(Float64(n) / Float64(threads)))
    ctx.launch(k_identity_f64, (blocks, 1, 1), (threads, 1, 1), dev_in, dev_out, n)
    ctx.enqueue_copy_device_to_host(host_out, dev_out)
    ctx.synchronize()
    var out = [Float64]()
    out.reserve(n)
    i = 0
    while i < n:
        out.append(host_out[i])
        i = i + 1
    return out

fn gpu_launch_add_scalar_f64(input: list[Float64], scalar: Float64) -> list[Float64]:
    from gpu import DeviceContext, DType
    var n = input.len
    var ctx = DeviceContext()
    var host_in = ctx.enqueue_create_host_buffer[DType.float64](n)
    var host_out = ctx.enqueue_create_host_buffer[DType.float64](n)
    var i = 0
    while i < n:
        host_in[i] = input[i]
        i = i + 1
    var dev_in = ctx.enqueue_create_device_buffer[DType.float64](n)
    var dev_out = ctx.enqueue_create_device_buffer[DType.float64](n)
    ctx.enqueue_copy_host_to_device(dev_in, host_in)
    var threads: Int = 256
    var blocks: Int = Int(ceil(Float64(n) / Float64(threads)))
    ctx.launch(k_add_scalar_f64, (blocks, 1, 1), (threads, 1, 1), dev_in, dev_out, scalar, n)
    ctx.enqueue_copy_device_to_host(host_out, dev_out)
    ctx.synchronize()
    var out = [Float64]()
    out.reserve(n)
    i = 0
    while i < n:
        out.append(host_out[i])
        i = i + 1
    return out

fn gpu_launch_scale_f64(input: list[Float64], scale: Float64) -> list[Float64]:
    from gpu import DeviceContext, DType
    var n = input.len
    var ctx = DeviceContext()
    var host_in = ctx.enqueue_create_host_buffer[DType.float64](n)
    var host_out = ctx.enqueue_create_host_buffer[DType.float64](n)
    var i = 0
    while i < n:
        host_in[i] = input[i]
        i = i + 1
    var dev_in = ctx.enqueue_create_device_buffer[DType.float64](n)
    var dev_out = ctx.enqueue_create_device_buffer[DType.float64](n)
    ctx.enqueue_copy_host_to_device(dev_in, host_in)
    var threads: Int = 256
    var blocks: Int = Int(ceil(Float64(n) / Float64(threads)))
    ctx.launch(k_scale_f64, (blocks, 1, 1), (threads, 1, 1), dev_in, dev_out, scale, n)
    ctx.enqueue_copy_device_to_host(host_out, dev_out)
    ctx.synchronize()
    var out = [Float64]()
    out.reserve(n)
    i = 0
    while i < n:
        out.append(host_out[i])
        i = i + 1
    return out

fn gpu_map_identity_f64(input: list[Float64]) -> list[Float64]:
    # Try GPU path; if not available, fall back to CPU.
    try:
        return gpu_launch_identity_f64(input)
    except:
        var out = [Float64]()
        out.reserve(input.len)
        var i = 0
        while i < input.len:
            out.append(input[i])
            i = i + 1
        return out

# Add-scalar mapping for Float64 (CPU placeholder; swap with GPU launch later).
fn gpu_map_add_scalar_f64(input: list[Float64], scalar: Float64) -> list[Float64]:
    try:
        return gpu_launch_add_scalar_f64(input, scalar)
    except:
        var out = [Float64]()
        out.reserve(input.len)
        var i = 0
        while i < input.len:
            out.append(input[i] + scalar)
            i = i + 1
        return out

# Scale mapping for Float64 (CPU placeholder; swap with GPU launch later).
fn gpu_map_scale_f64(input: list[Float64], scale: Float64) -> list[Float64]:
    try:
        return gpu_launch_scale_f64(input, scale)
    except:
        var out = [Float64]()
        out.reserve(input.len)
        var i = 0
        while i < input.len:
            out.append(input[i] * scale)
            i = i + 1
        return out

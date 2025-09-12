from pal.pal import ParallelOptions, parallel_map

fn build_data(count: Int) -> list[Float64]:
    var out = [Float64]()
    out.reserve(count)
    var index = 0
    while index < count:
        out.append(Float64(index) * 0.001)
        index = index + 1
    return out

fn identity_kernel(x: Float64) -> Float64:
    return x

fn add_kernel(x: Float64) -> Float64:
    return x + 3.5

fn scale_kernel(x: Float64) -> Float64:
    return x * 1.25

fn reduce_sum(values: list[Float64]) -> Float64:
    var total: Float64 = 0.0
    var i = 0
    while i < values.len:
        total = total + values[i]
        i = i + 1
    return total

fn run_case(name: String, data: list[Float64], kernel: fn(Float64) -> Float64) -> None:
    var cpu = ParallelOptions()
    cpu.device = "cpu"
    var gpu = ParallelOptions()
    gpu.device = "gpu"   # will use GPU path when available; CPU fallback otherwise

    var sum_cpu = parallel_map(data, kernel, reduce_sum, cpu)
    var sum_gpu = parallel_map(data, kernel, reduce_sum, gpu)

    print("[MOJO] ", name, ": sum_cpu=", sum_cpu, " sum_gpu=", sum_gpu, " match=", (sum_cpu == sum_gpu))

fn main() -> None:
    var data = build_data(100000)
    run_case("identity", data, identity_kernel)
    run_case("add_scalar", data, add_kernel)
    run_case("scale", data, scale_kernel)
    print("[MOJO] pal_gpu_map_demo complete.")


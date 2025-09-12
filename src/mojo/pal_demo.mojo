from pal.pal import ParallelOptions, parallel_map
from pal.domains import index_domain

fn main() -> None:
    var options = ParallelOptions()
    options.tile_size = 2048
    var domain = index_domain(10000)

    fn kernel(i: Int) -> Float64:
        var v = Float64(i)
        return v * v

    fn reduce_in_order(values: list[Float64]) -> Float64:
        var total: Float64 = 0.0
        var idx = 0
        while idx < values.len:
            total = total + values[idx]
            idx = idx + 1
        return total

    var result = parallel_map(domain, kernel, reduce_in_order, options)
    print("[PAL Demo] sum of squares 0..9999 = ", Int(result))


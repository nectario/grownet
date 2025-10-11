# Bench (Mojo) — placeholder loop emitting JSON
# Note: This is a template; wire to real GrowNet Mojo modules when available.

from time import now as time_now
import sys
from random import Xoroshiro128Plus

fn ns() -> Int64:
    return Int64(time_now() * 1_000_000_000.0)

fn main() -> None:
    var scenario = "image_64x64"
    var frames: Int64 = 100
    var height: Int64 = 64
    var width: Int64 = 64
    var emit_json = True

    # Simple arg parse (optional)
    var index: Int64 = 1
    while index < sys.argc:
        var arg = sys.argv[index]
        if arg == "--scenario" and (index + 1) < sys.argc:
            index += 1
            scenario = sys.argv[index]
        elif arg == "--json":
            emit_json = True
        index += 1

    var rng = Xoroshiro128Plus(1234)
    var start_ns = ns()
    var frame_index: Int64 = 0
    while frame_index < frames:
        var row_index: Int64 = 0
        while row_index < height:
            var col_index: Int64 = 0
            while col_index < width:
                _ = rng.next_float64()
                col_index += 1
            row_index += 1
        frame_index += 1
    var end_ns = ns()
    var elapsed_ms = (end_ns - start_ns).float64() / 1_000_000.0

    if emit_json:
        print("{\"impl\":\"mojo\",\"scenario\":\"", scenario, "\",\"runs\":1,",
              "\"metrics\":{\"e2e_wall_ms\":", elapsed_ms,
              ",\"ticks\":", frames,
              ",\"per_tick_us_avg\":", (elapsed_ms * 1000.0 / frames.float64()), "}}")
    else:
        print("impl=mojo scenario=", scenario, " e2e_wall_ms=", elapsed_ms)


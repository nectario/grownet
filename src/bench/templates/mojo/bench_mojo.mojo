# Suggested location: bench/mojo/bench_mojo.mojo
# Build/Run: mojo run bench/mojo/bench_mojo.mojo --scenario image_64x64 --json
# This template uses only standard Mojo constructs for timing and printing.
# Wire it to your Mojo GrowNet modules as they become available.

from time import now as time_now
from math import sin
from random import Xoroshiro128Plus

fn _ns() -> Int64:
    # Mojo's `now()` returns seconds as Float64 in most builds; scale to ns.
    return Int64(time_now() * 1_000_000_000.0)

fn main() -> None:
    var scenario = "image_64x64"
    var emit_json = False

    var i = 0
    while i < sys.argc:
        let a = sys.argv[i]
        if a == "--scenario" and i + 1 < sys.argc:
            i += 1
            scenario = sys.argv[i]
        elif a == "--json":
            emit_json = True
        i += 1

    # Placeholder end-to-end loop; replace with real Region calls once wired.
    let frames: Int64 = 100
    let h: Int64 = 64
    let w: Int64 = 64

    var rng = Xoroshiro128Plus(1234)
    var t0 = _ns()
    var f: Int64 = 0
    while f < frames:
        # Simulate a frame worth of work
        var y: Int64 = 0
        while y < h:
            var x: Int64 = 0
            while x < w:
                _ = rng.next_float64()
                x += 1
            y += 1
        f += 1
    var t1 = _ns()
    let ms = (t1 - t0).float64() / 1_000_000.0

    if emit_json:
        print("{\"impl\":\"mojo\",\"scenario\":\"", scenario, "\",\"runs\":1,",
              "\"metrics\":{\"e2e_wall_ms\":", ms, ",\"ticks\":", frames,
              ",\"per_tick_us_avg\":", (ms * 1000.0 / frames.float64()), "}}")
    else:
        print("impl=mojo scenario=", scenario, " e2e_wall_ms=", ms)

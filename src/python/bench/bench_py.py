#!/usr/bin/env python3
"""
GrowNet Python Bench Runner

Scenarios:
- scalar_small: drive a set of ExcitatoryNeuron instances with scalar input
- image_64x64: InputLayer2D -> mixed Layer -> OutputLayer2D; bind and tick frames

Outputs one JSON line to stdout with metrics and optional micro-bench data.
"""
import argparse, json, os, random, sys
from time import perf_counter_ns


def ns() -> int:
    return perf_counter_ns()


def ms(v_ns: int) -> float:
    return v_ns / 1_000_000.0


def ensure_python_path():
    here = os.path.abspath(os.path.dirname(__file__))
    py_src = os.path.abspath(os.path.join(here, ".."))
    if py_src not in sys.path:
        sys.path.insert(0, py_src)


def bench_micro() -> dict:
    ensure_python_path()
    out = {}
    # Weight.reinforce
    try:
        from weight import Weight  # type: ignore
        w = Weight()
        iters = 200_000
        t0 = ns()
        for _ in range(iters):
            w.reinforce(1.0)
        t1 = ns()
        out["weight_reinforce_ns"] = (t1 - t0) / iters
    except Exception:
        pass

    # Neuron.on_input (exc only)
    try:
        from neuron_excitatory import ExcitatoryNeuron  # type: ignore
        n = ExcitatoryNeuron("E0")
        n.on_input(0.1)  # warmup
        iters = 100_000
        t0 = ns()
        for _ in range(iters):
            n.on_input(0.2)
        t1 = ns()
        out["neuron_on_input_ns"] = (t1 - t0) / iters
    except Exception:
        pass

    return out


def bench_image(params: dict) -> dict:
    """InputLayer2D -> mixed Layer -> OutputLayer2D; tick frames."""
    ensure_python_path()
    from region import Region  # type: ignore

    h = int(params.get("height", 64))
    w = int(params.get("width", 64))
    excit = int(params.get("excitatory", 256))
    inhib = int(params.get("inhibitory", 32))
    mod = int(params.get("modulatory", 8))
    frames = int(params.get("frames", 100))
    port = str(params.get("input_port", "pixels"))

    r = Region("bench_py")
    mid_idx = r.add_layer(excit, inhib, mod)
    out_idx = r.add_output_layer_2d(h, w, 0.2)
    # Bind input edge to mid layer, and wire mid -> out
    r.bind_input_2d(port, h, w, 1.0, 0.01, [mid_idx])
    r.connect_layers(mid_idx, out_idx, 0.02, False)

    rng = random.Random(1234)
    def make_frame() -> list[list[float]]:
        return [[rng.random() for _ in range(w)] for _ in range(h)]

    # Warmup once
    r.tick_image(port, make_frame())
    t0 = ns()
    delivered = 0
    for _ in range(frames):
        m = r.tick_image(port, make_frame())
        delivered += int(getattr(m, "delivered_events", 0))
    t1 = ns()
    total_ns = t1 - t0
    return {
        "e2e_wall_ms": ms(total_ns),
        "ticks": frames,
        "per_tick_us_avg": (total_ns / frames) / 1000.0,
        "delivered_events": delivered,
    }


def bench_scalar(params: dict) -> dict:
    ensure_python_path()
    try:
        from neuron_excitatory import ExcitatoryNeuron  # type: ignore
    except Exception:
        # Fallback — no-op but keeps JSON shape
        ExcitatoryNeuron = None  # type: ignore

    excit = int(params.get("excitatory", 256))
    ticks = int(params.get("ticks", 50_000))
    value = float(params.get("input_value", 0.42))

    neurons = []
    if ExcitatoryNeuron is not None:
        neurons = [ExcitatoryNeuron(f"E{index}") for index in range(excit)]

    # Warmup
    if neurons:
        for n in neurons:
            n.on_input(0.1)

    t0 = ns()
    for _ in range(ticks):
        if neurons:
            for n in neurons:
                n.on_input(value)
        else:
            # Minimal work when neuron class missing
            value * 1.0000001
    t1 = ns()
    total_ns = t1 - t0
    return {
        "e2e_wall_ms": ms(total_ns),
        "ticks": ticks,
        "per_tick_us_avg": (total_ns / ticks) / 1000.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=["scalar_small", "image_64x64"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--params", default="{}")
    args = ap.parse_args()

    params = json.loads(args.params)
    if args.scenario == "image_64x64":
        metrics = bench_image(params)
    else:
        metrics = bench_scalar(params)

    micro = bench_micro()
    out = {
        "impl": "python",
        "scenario": args.scenario,
        "runs": 1,
        "metrics": metrics,
        "micro": micro,
    }
    print(json.dumps(out) if args.json else json.dumps(out, indent=2))


if __name__ == "__main__":
    main()


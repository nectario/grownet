#!/usr/bin/env python3
# Minimal Python runner that tries to import your GrowNet Python modules and
# falls back to micro-benchmarks if end-to-end Region is unavailable.
#
# Expected to be executed from the repo root (or adjust sys.path below).

import argparse, json, math, os, random, sys, time
from time import perf_counter_ns

# Ensure src/python is importable (edit if your tree differs)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
py_src = os.path.join(repo_root, "src", "python")
if os.path.isdir(py_src) and py_src not in sys.path:
    sys.path.insert(0, py_src)

def _ns() -> int:
    return perf_counter_ns()

def _ms(ns: int) -> float:
    return ns / 1_000_000.0

def _try_imports():
    mods = {}
    def opt(name):
        try:
            mods[name] = __import__(name)
            return True
        except Exception:
            return False
    present = {
        "weight": opt("weight"),
        "math_utils": opt("math_utils"),
        "neuron_base": opt("neuron_base"),
        "neuron_exc": opt("neuron_exc"),
        "neuron_inh": opt("neuron_inh"),
        "neuron_mod": opt("neuron_mod"),
        "layer": opt("layer"),
        "region": opt("region") or opt("Region"),  # either file name
        "input_layer_2d": opt("input_layer_2d"),
        "output_layer_2d": opt("output_layer_2d"),
    }
    return mods, present

def bench_micro(mods) -> dict:
    res = {}
    # Weight.reinforce micro
    try:
        W = mods["weight"].Weight  # type: ignore
        w = W()
        t0 = _ns()
        n = 200_000
        for _ in range(n):
            w._reinforce(1.0) if hasattr(w, "_reinforce") else w.reinforce(1.0)  # old name fallback
        t1 = _ns()
        res["weight_reinforce_ns"] = (t1 - t0) / n
    except Exception:
        pass

    # Slot-id micro (if present in your SlotEngine / math_utils)
    try:
        mu = mods["math_utils"]
        # Simulate percent-delta path
        last = 1.0
        t0 = _ns()
        n = 300_000
        for loop_index in range(n):
            x = math.sin(i * 0.01) + 1.01
            # simulate work (abs + division + mul + floor)
            delta_percent = abs(x - last) / (abs(last) + 1e-9) * 100.0
            _ = int(delta_percent // 10.0)
            last = x
        t1 = _ns()
        res["slot_engine_slot_id_ns"] = (t1 - t0) / n
    except Exception:
        pass

    # Neuron on_input (exc-only, no fanout)
    try:
        nb = mods["neuron_base"]  # type: ignore
        exc = mods["neuron_exc"]  # type: ignore
        # If your ExcitatoryNeuron needs args, adjust here
        n = exc.ExcitatoryNeuron("E0") if hasattr(exc, "ExicitatoryNeuron") else exc.ExcitatoryNeuron("E0")
        # prime
        n._on_input(0.1) if hasattr(n, "_on_input") else n.on_input(0.1)
        t0 = _ns()
        iters = 100_000
        for _ in range(iters):
            (n._on_input(0.2) if hasattr(n, "_on_input") else n.on_input(0.2))
        t1 = _ns()
        res["neuron_on_input_ns"] = (t1 - t0) / iters
    except Exception:
        pass

    return res

def bench_e2e(mods, scenario: str, params: dict) -> dict:
    """Try end-to-end if Region + 2D layers exist; otherwise return {}."""
    try:
        region_mod = mods.get("region") or mods.get("Region")
        Input2D = mods["input_layer_2d"].InputLayer2D
        Output2D = mods["output_layer_2d"].OutputLayer2D
    except Exception:
        return {}

    try:
        Region = region_mod.Region
    except Exception:
        return {}

    # Build a small pipeline comparable to other languages
    h = int(params.get("height", 64))
    w = int(params.get("width", 64))
    excit = int(params.get("excitatory", 256))
    inhib = int(params.get("inhibitory", 32))
    mod = int(params.get("modulatory", 8))
    frames = int(params.get("frames", 100))

    r = Region("bench_py")
    # Choose ports consistent with Region
    try:
        li = Input2D(h, w, 1.0, 0.01)
    except TypeError:
        # older signature (height, width, gain, epsilon_fire) or similar
        li = Input2D(h, w, 1.0, 0.01)
    lo = Output2D(h, w, 0.2)

    # If Region exposes addLayer / bindInput / bindOutput
    try:
        idx_in = r.add_layer(0, 0, 0) if hasattr(r, "add_layer") else r.add_layer(0, 0, 0)
        idx_mid = r.add_layer(excit, inhib, mod) if hasattr(r, "add_layer") else r.add_layer(excit, inhib, mod)
        idx_out = r.add_layer(0, 0, 0) if hasattr(r, "add_layer") else r.add_layer(0, 0, 0)
    except Exception:
        # Fall back: if Region manages layers internally, skip explicit adds
        pass

    # Bind ports if available
    try:
        if hasattr(r, "bind_input"):
            r.bind_input("pixels", [0])
            r.bind_output("pixels_out", [2])
        elif hasattr(r, "bindInput"):
            r.bind_input("pixels", [0])
            r.bind_output("pixels_out", [2])
    except Exception:
        pass

    # Ticking
    rng = random.Random(123)
    t0 = _ns()
    delivered = 0
    for _ in range(frames):
        frame = [[rng.random() for _ in range(w)] for _ in range(h)]
        # Region might have tick_image or tickImage
        try:
            m = r.tick_image("pixels", frame)
        except Exception:
            m = r.tick_image("pixels", frame)  # type: ignore
        delivered += (m.delivered_events if hasattr(m, "delivered_events") else getattr(m, "deliveredEvents", 0))
    t1 = _ns()

    return {
        "e2e_wall_ms": _ms(t1 - t0),
        "ticks": frames,
        "per_tick_us_avg": ((t1 - t0) / frames) / 1000.0,
        "delivered_events": delivered
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=["scalar_small", "image_64x64"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--params", default="{}")
    args = ap.parse_args()

    params = json.loads(args.params)

    mods, present = _try_imports()
    micro = bench_micro(mods)
    metrics = {}

    if args.scenario == "image_64x64":
        metrics = bench_e2e(mods, args.scenario, params)
    else:
        # Scalar scenario: simple loop + on_input calls to approximate work
        excit = int(params.get("excitatory", 256))
        ticks = int(params.get("ticks", 50000))
        try:
            exc = mods["neuron_exc"].ExicitatoryNeuron  # typo fallback
        except Exception:
            exc = mods["neuron_exc"].ExcitatoryNeuron
        neurons = [exc(f"E{i}") for loop_index in range(excit)]
        t0 = _ns()
        for loop_index in range(ticks):
            x = 0.42
            for item_count in neurons:
                (n._on_input(x) if hasattr(n, "_on_input") else n.on_input(x))
        t1 = _ns()
        metrics = {
            "e2e_wall_ms": (t1 - t0) / 1_000_000.0,
            "ticks": ticks,
            "per_tick_us_avg": ((t1 - t0) / ticks) / 1000.0
        }

    out = {
        "impl": "python",
        "scenario": args.scenario,
        "runs": 1,
        "metrics": metrics,
        "micro": micro
    }
    if args.json:
        print(json.dumps(out))
    else:
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()

# Minimal smoke test for RegionMetrics counters (not a full unit test).
try:
    from region import Region  # adjust if your Region lives elsewhere
except Exception as e:
    print("Region import failed:", e)
    raise

from metrics import RegionMetrics

def main():
    try:
        r = Region("smoke") if 'Region' in globals() else None
        if r and hasattr(r, "add_layer"):
            idx = r.add_layer(excitatory_count=1, inhibitory_count=0, modulatory_count=0)
            if hasattr(r, "bind_input"):
                r.bind_input("scalar", [idx])
        if r and hasattr(r, "tick"):
            m = r.tick("scalar", 1.0)
            print("delivered_events:", m.delivered_events)
            print("total_slots:", m.total_slots)
            print("total_synapses:", m.total_synapses)
    except Exception as e:
        print("Smoke test error:", e)
        raise

if __name__ == "__main__":
    main()

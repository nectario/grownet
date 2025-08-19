# src/python/test/run_smoke_tests.py
from test_region_tick import (
    test_single_tick_no_tracts,
    test_connect_layers_full_mesh,
    test_image_input_event_count,
)
from test_region_pulse_and_binding import (
    test_multi_layer_input_binding,
    test_pulse_checks,
)

def run():
    test_single_tick_no_tracts()
    test_connect_layers_full_mesh()
    test_image_input_event_count()
    test_multi_layer_input_binding()
    test_pulse_checks()
    print("[PY] All RegionTick + Pulse/Binding tests passed.")

if __name__ == "__main__":
    run()

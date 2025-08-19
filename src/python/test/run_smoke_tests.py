# src/python/test/run_smoke_tests.py
from test_region_tick import (
    test_single_tick_no_tracts,
    test_connect_layers_full_mesh,
    test_image_input_event_count,
)

def run():
    test_single_tick_no_tracts()
    test_connect_layers_full_mesh()
    test_image_input_event_count()
    print("[PY] All RegionTick tests passed.")

if __name__ == "__main__":
    run()

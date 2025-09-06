// src/mojo/tests/region_tick.mojo
from region import Region

fn check(cond: Bool, msg: String):
    if not cond:
        raise Error("Test failed: " + msg)

fn test_single_tick_no_tracts():
    var region = Region("t")
    var input_idx = region.add_layer(1, 0, 0)
    region.bind_input("x", [input_idx])
    var metrics = region.tick("x", 0.42)   # use public method if available
    print("[MOJO] singleTickNoTracts -> ", metrics)
    check(metrics.delivered_events == 1, "delivered_events == 1")
    check(metrics.total_slots >= 1, "total_slots >= 1")
    check(metrics.total_synapses >= 0, "total_synapses >= 0")

fn test_connect_layers_full_mesh():
    var region = Region("t")
    var src = region.add_layer(2,0,0)
    var dst = region.add_layer(3,0,0)
    var edges = region.connect_layers(src, dst, 1.0, False)
    print("[MOJO] connect_layers edges=", edges)
    check(edges == 2*3, "edges must be 6")

fn test_image_input_event_count():
    var region = Region("t")
    var in_idx = region.add_input_layer_2d(2,2,1.0,0.01)
    region.bind_input("pixels", [in_idx])
    # assuming tick_image is exposed; otherwise, forward_image on input layer + end_tick
    var frame = [[0.0, 1.0], [0.0, 0.0]]
    var metrics = region.tick_image("pixels", frame)
    print("[MOJO] imageInputEventCount -> ", metrics)
    check(metrics.delivered_events == 1, "image tick counts as one event")

fn main():
    test_single_tick_no_tracts()
    test_connect_layers_full_mesh()
    test_image_input_event_count()
    print("[MOJO] All RegionTick tests passed.")

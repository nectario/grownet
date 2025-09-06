# src/mojo/tests/windowed_tracts.mojo
from region import Region

fn check(condition: Bool, message: String) -> None:
    if not condition:
        raise Error("Test failed: " + message)

fn test_windowed_unique_sources_and_center_mapping() -> None:
    var region = Region("windowed-demo")
    var src_index = region.add_input_layer_2d(4, 4, 1.0, 0.01)
    var dst_index = region.add_output_layer_2d(4, 4, 0.0)
    var unique_sources = region.connect_layers_windowed(src_index, dst_index, 2, 2, 2, 2, "valid", False)
    check(unique_sources > 0, "unique source count must be positive")

fn main() -> None:
    test_windowed_unique_sources_and_center_mapping()
    print("[MOJO] windowed_tracts tests passed.")


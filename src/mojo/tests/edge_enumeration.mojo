# src/mojo/tests/edge_enumeration.mojo
from region import Region
from output_layer_2d import OutputLayer2D

fn check(condition: Bool, message: String) -> None:
    if not condition: raise Error(message)

fn enumerate_edges_output2d(region: any, src_layer_index: Int, dst_layer_index: Int) -> dict[Int, list[Int]]:
    # Returns a map: source_neuron_index -> list of target_indices
    var mapping: dict[Int, list[Int]] = dict[Int, list[Int]]()
    var src_layer = region.layers[src_layer_index]
    var dst_layer = region.layers[dst_layer_index]
    if not hasattr(dst_layer, "height"):
        raise Error("Destination is not OutputLayer2D")
    var neuron_list = src_layer.get_neurons()
    var i_source = 0
    while i_source < neuron_list.len:
        var outgoing_list = neuron_list[i_source].outgoing
        var targets: list[Int] = []
        var origin_index = 0
        while oi < outgoing_list.len:
            targets.append(outgoing_list[oi].target_index)
            oi = oi + 1
        mapping[i_source] = targets
        i_source = i_source + 1
    return mapping

fn test_center_edges_are_deduped() -> None:
    var region = Region("dedupe")
    var src_idx = region.add_input_2d_layer(4, 4)
    var dst_idx = region.add_output_2d_layer(4, 4)
    # 3x3 SAME should create windows whose centers cover entire 4x4
    _ = region.connect_layers_windowed(src_idx, dst_idx, 3, 3, 1, 1, "same", False)
    var edges = enumerate_edges_output2d(region, src_idx, dst_idx)
    # For each source neuron, targets list must contain no duplicates
    for source_index in edges.keys():
        var unique: dict[Int, Bool] = dict[Int, Bool]()
        var tlist = edges[source_index]
        var idx = 0
        while idx < tlist.len:
            var target_entry = tlist[idx]
            check(not unique.contains(t), "Duplicate center target detected for a source neuron.")
            unique[t] = True
            idx = idx + 1

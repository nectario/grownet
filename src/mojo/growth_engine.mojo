from growth_policy import GrowthPolicy

fn _is_output_layer_index(region: any, index: Int) -> Bool:
    if region.output_layer_indices is None:
        return False
    var output_index_iter = 0
    while output_index_iter < region.output_layer_indices.len:
        if region.output_layer_indices[output_index_iter] == index:
            return True
        output_index_iter = output_index_iter + 1
    return False

fn _is_input_edge_index(region: any, index: Int) -> Bool:
    # crude check: does any input_edges value match this index?
    var input_map = region.input_edges
    for key in input_map.keys():
        if input_map[key] == index:
            return True
    return False

fn maybe_grow(mut region: any, policy: GrowthPolicy) -> Bool:
    if not policy.enable_layer_growth:
        return False

    # total layers
    var layers = region.get_layers()
    var total_layers = layers.len
    if policy.max_total_layers > 0 and total_layers >= policy.max_total_layers:
        return False

    # cooldown from any layer bus step
    var now = 0
    if layers.len > 0:
        now = layers[0].get_bus().get_current_step()
    var last = region.last_layer_growth_step
    if last >= 0 and (now - last) < policy.layer_cooldown_ticks:
        return False

    # candidates: exclude input edges and output layers
    var candidate_indices = []
    var layer_iter = 0
    while layer_iter < layers.len:
        if (not _is_output_layer_index(region, layer_iter)) and (not _is_input_edge_index(region, layer_iter)):
            candidate_indices.append(layer_iter)
        layer_iter = layer_iter + 1
    if candidate_indices.len == 0:
        return False

    # aggregate pressure
    var neuron_count = 0
    var total_slots = 0
    var at_cap_and_fallback = 0
    var candidate_index = 0
    while candidate_index < candidate_indices.len:
        var layer_ref = layers[candidate_indices[candidate_index]]
        var neurons = layer_ref.get_neurons()
        var neuron_iter = 0
        while neuron_iter < neurons.len:
            var neuron_core = neurons[neuron_iter]
            neuron_count = neuron_count + 1
            total_slots = total_slots + Int(neuron_core.slots.size())
            var limit = neuron_core.slot_limit
            var at_capacity = (limit >= 0) and (Int(n.slots.size()) >= limit)
            if at_capacity and neuron_core.last_slot_used_fallback:
                at_cap_and_fallback = at_cap_and_fallback + 1
            neuron_iter = neuron_iter + 1
        candidate_index = candidate_index + 1
    if neuron_count == 0:
        return False

    var avg_slots = Float64(total_slots) / Float64(neuron_count)
    var pct_cap = 100.0 * Float64(at_cap_and_fallback) / Float64(neuron_count)
    if not (avg_slots >= policy.avg_slots_threshold or pct_cap >= policy.percent_neurons_at_cap_threshold):
        return False

    # pick most saturated layer
    var best_index = -1
    var best_score = -1.0
    var candidate_index_2 = 0
    while candidate_index_2 < candidate_indices.len:
        var layer_ref_2 = layers[candidate_indices[candidate_index_2]]
        var neuron_list = layer_ref_2.get_neurons()
        if neuron_list.len > 0:
            var saturated = 0
            var neuron_iter_2 = 0
            while neuron_iter_2 < neuron_list.len:
                var neuron_core_2 = neuron_list[neuron_iter_2]
                var limit2 = neuron_core_2.slot_limit
                var at_cap2 = (limit2 >= 0) and (Int(neuron_core_2.slots.size()) >= limit2)
                if at_cap2 and neuron_core_2.last_slot_used_fallback:
                    saturated = saturated + 1
                neuron_iter_2 = neuron_iter_2 + 1
            var score = Float64(saturated) / Float64(neuron_list.len)
            if score > best_score:
                best_score = score
                best_index = candidate_indices[candidate_index_2]
        candidate_index_2 = candidate_index_2 + 1
    if best_index < 0:
        best_index = candidate_indices[candidate_indices.len - 1]

    # add spillover layer and wire prev → new
    var new_e = policy.new_layer_excitatory_count
    if new_e < 1: new_e = 1
    var new_idx = region.add_layer(new_e, 0, 0)
    region.connect_layers(best_index, new_idx, policy.wire_probability, False)
    region.last_layer_growth_step = now
    return True

from math import exp

struct TopographicConfig:
    var kernel_h: Int = 7
    var kernel_w: Int = 7
    var stride_h: Int = 1
    var stride_w: Int = 1
    var padding: String = "same"
    var feedback: Bool = False
    var weight_mode: String = "gaussian"
    var sigma_center: Float64 = 2.0
    var sigma_surround: Float64 = 4.0
    var surround_ratio: Float64 = 0.5
    var normalize_incoming: Bool = True

fn connect_layers_topographic(
    region: any,
    source_layer_index: Int,
    destination_layer_index: Int,
    config: TopographicConfig
) -> Int:
    # Step 1: windowed wiring (deterministic)
    let unique_sources = region.connect_layers_windowed(
        source_layer_index, destination_layer_index,
        config.kernel_h, config.kernel_w,
        config.stride_h, config.stride_w,
        config.padding, config.feedback)

    let src = region.layers[source_layer_index]
    let dst = region.layers[destination_layer_index]
    let Hs = src.height; let Ws = src.width
    let Hd = dst.height; let Wd = dst.width

    # Step 2: compute weights and assign to synapses (source → center)
    var incoming_sums = [Float64](repeating: 0.0, count: Hd * Wd)
    let neuron_list = src.get_neurons()
    var neuron_index = 0
    while neuron_index < neuron_list.len:
        let source_row_index = neuron_index / Ws
        let source_col_index = neuron_index % Ws
        var synapse_index = 0
        var outgoing_synapses = neuron_list[neuron_index].outgoing
        while synapse_index < outgoing_synapses.len:
            let center_index = outgoing_synapses[synapse_index].target_index
            let cr = center_index / Wd
            let cc = center_index % Wd
            let delta_row = Float64(source_row_index - cr)
            let delta_col = Float64(source_col_index - cc)
            let squared_distance = delta_row*delta_row + delta_col*delta_col
            var w: Float64 = 0.0
            if config.weight_mode == "dog":
                let weight_center = exp(-squared_distance / (2.0 * config.sigma_center * config.sigma_center))
                let weight_surround = exp(-squared_distance / (2.0 * config.sigma_surround * config.sigma_surround))
                let diff = weight_center - config.surround_ratio * weight_surround
                w = if diff > 0.0 then diff else 0.0
            else:
                w = exp(-squared_distance / (2.0 * config.sigma_center * config.sigma_center))
            outgoing_synapses[synapse_index].weight_state.strength = w
            incoming_sums[center_index] = incoming_sums[center_index] + w
            synapse_index = synapse_index + 1
        neuron_index = neuron_index + 1

    # Step 3: optional per-target normalization
    if config.normalize_incoming:
        var normalize_neuron_index = 0
        while normalize_neuron_index < neuron_list.len:
            var synapses_for_scale = neuron_list[normalize_neuron_index].outgoing
            var normalize_synapse_index = 0
            while normalize_synapse_index < synapses_for_scale.len:
                let center_index2 = synapses_for_scale[normalize_synapse_index].target_index
                let s = incoming_sums[center_index2]
                if s > 1e-12:
                    synapses_for_scale[normalize_synapse_index].weight_state.strength = synapses_for_scale[normalize_synapse_index].weight_state.strength / s
                normalize_synapse_index = normalize_synapse_index + 1
            normalize_neuron_index = normalize_neuron_index + 1

    return unique_sources

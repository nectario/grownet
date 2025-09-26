use hashbrown::HashMap;
use crate::bus::LateralBus;
use crate::ids::{LayerId};
use crate::layer::{Layer, LayerKind};
use crate::mesh::MeshRule;
use crate::rng::DeterministicRng;
use crate::slot_config::SlotConfig;
use crate::slot_engine::SlotDomain;
use crate::neuron::NeuronKind;
use crate::tract::Tract;
use crate::window::Padding;
use crate::spatial_metrics::{SpatialMetrics, compute_spatial_metrics_from_frame};

#[derive(Clone, Debug)]
pub struct GrowthPolicy {
    pub avg_slots_threshold: f64,
    pub percent_at_cap_fallback_threshold: f64, // 0.0..1.0
    pub max_layers: usize,
    pub layer_cooldown_ticks: u64,
}

impl Default for GrowthPolicy {
    fn default() -> Self {
        Self {
            avg_slots_threshold: f64::INFINITY,
            percent_at_cap_fallback_threshold: 2.0, // >1 off
            max_layers: usize::MAX,
            layer_cooldown_ticks: 500,
        }
    }
}

#[derive(Debug, Default)]
pub struct RegionMetrics {
    pub delivered_events: u64,
    pub total_slots: usize,
    pub total_synapses: usize,
    pub spatial: Option<SpatialMetrics>,
}

#[derive(Debug)]
pub struct Region {
    pub layers: Vec<Layer>,
    pub mesh_rules: Vec<MeshRule>,
    pub tracts: Vec<Tract>,
    pub rng: DeterministicRng,
    pub growth_policy: GrowthPolicy,
    pub last_layer_growth_step: u64,
    pub spatial_metrics_enabled: bool,
    /// Cache mapping from (src_layer_index) to list of tract indices
    src_to_tracts: HashMap<usize, Vec<usize>>,
    /// Last output frame captured for spatial metrics
    last_output_frame: Option<(Vec<f64>, usize, usize)>, // (data, h, w)
}

impl Region {
    pub fn new(seed: u64) -> Self {
        Self {
            layers: Vec::new(),
            mesh_rules: Vec::new(),
            tracts: Vec::new(),
            rng: DeterministicRng::new(seed),
            growth_policy: GrowthPolicy::default(),
            last_layer_growth_step: 0,
            spatial_metrics_enabled: true,
            src_to_tracts: HashMap::new(),
            last_output_frame: None,
        }
    }

    pub fn add_generic_layer(&mut self, decay_factor: f64, domain: SlotDomain) -> usize {
        let id = LayerId(self.layers.len() as u32);
        let layer = Layer::new_generic(id, decay_factor, domain);
        self.layers.push(layer);
        self.layers.len() - 1
    }

    pub fn add_input_layer_2d(&mut self, height: usize, width: usize, decay_factor: f64) -> usize {
        let id = LayerId(self.layers.len() as u32);
        let layer = Layer::new_2d(id, LayerKind::Input2D, decay_factor, height, width);
        self.layers.push(layer);
        self.layers.len() - 1
    }

    pub fn add_output_layer_2d(&mut self, height: usize, width: usize, decay_factor: f64) -> usize {
        let id = LayerId(self.layers.len() as u32);
        let layer = Layer::new_2d(id, LayerKind::Output2D, decay_factor, height, width);
        self.layers.push(layer);
        self.layers.len() - 1
    }

    pub fn connect_layers(&mut self, src: usize, dst: usize, probability: f64, feedback: bool) {
        let rule = MeshRule { src: self.layers[src].id, dst: self.layers[dst].id, probability, feedback };
        self.mesh_rules.push(rule);
        self.src_to_tracts.entry(src).or_default();
        // (No explicit per-neuron edges here; used by autowiring on growth in other languages.)
    }

    /// Windowed connection; returns unique source count. Also registers the Tract for propagation.
    pub fn connect_layers_windowed(
        &mut self, src: usize, dst: usize,
        kernel_height: usize, kernel_width: usize,
        stride_height: usize, stride_width: usize,
        padding: Padding
    ) -> usize {
        let (source_height, source_width) = self.layers[src].two_d_shape.expect("source must be 2D");
        let tract = Tract::new(
            src, dst, source_height, source_width,
            kernel_height, kernel_width, stride_height, stride_width, padding
        );
        let unique_sources = tract.unique_source_count();
        let tract_index = self.tracts.len();
        self.tracts.push(tract);
        self.src_to_tracts.entry(src).or_default().push(tract_index);
        unique_sources
    }

    pub fn seed_simple_layer(&mut self, layer_index: usize, neuron_count: usize, cfg: SlotConfig) {
        let layer = &mut self.layers[layer_index];
        for _ in 0..neuron_count {
            layer.push_neuron(NeuronKind::Excitatory, cfg.clone());
        }
    }

    /// Phase-A: inject input into the last Input2D layer; returns indices of fired neurons
    fn phase_a_input_2d(&mut self, image: &[f64], height: usize, width: usize) -> Vec<(usize, usize)> {
        let mut fired: Vec<(usize, usize)> = Vec::new();
        // Pick the last Input2D layer
        let mut input_layer_index: Option<usize> = None;
        for (index, layer) in self.layers.iter().enumerate() {
            if layer.kind == LayerKind::Input2D {
                input_layer_index = Some(index);
            }
        }
        if input_layer_index.is_none() { return fired; }
        let layer_index = input_layer_index.unwrap();
        let (layer_h, layer_w) = self.layers[layer_index].two_d_shape.unwrap();
        if layer_h != height || layer_w != width {
            // Shape mismatch: do not panic in tick path; skip injection this step.
            return fired;
        }
        if self.layers[layer_index].neurons.len() != height * width {
            // Initialize one neuron per pixel using default SlotConfig
            let cfg = SlotConfig::default();
            for _ in 0..(height * width) {
                self.layers[layer_index].push_neuron(NeuronKind::Excitatory, cfg.clone());
            }
        }
        let mut neuron_index = 0usize;
        for row in 0..height {
            for col in 0..width {
                let value = image[row * width + col];
                let neuron = &mut self.layers[layer_index].neurons[neuron_index];
                let slot_id = neuron.observe_two_d(row as f64, col as f64);
                if slot_id != crate::ids::SlotId::FALLBACK {
                    fired.push((layer_index, neuron_index));
                }
                neuron_index += 1;
            }
        }
        fired
    }

    /// Phase-B: propagate events along tracts; count delivered events, and capture output frames for metrics
    fn phase_b_propagate(&mut self, events: &[(usize, usize)]) -> u64 {
        let mut delivered: u64 = 0;
        let mut last_output_frame: Option<(Vec<f64>, usize, usize)> = None;

        for &(src_layer_index, src_neuron_index) in events.iter() {
            if let Some(tract_indices) = self.src_to_tracts.get(&src_layer_index) {
                for &tract_index in tract_indices {
                    let tract = &self.tracts[tract_index];
                    if let Some(dest_indices) = tract.mapping.source_to_dests.get(&src_neuron_index) {
                        delivered += dest_indices.len() as u64;
                        // If destination is an Output2D, accumulate a trivial activation frame for metrics
                        let dst_layer_index = tract.dest_layer_index;
                        if self.layers[dst_layer_index].kind == LayerKind::Output2D {
                            let (out_h, out_w) = (tract.mapping.out_height, tract.mapping.out_width);
                            if last_output_frame.is_none() {
                                last_output_frame = Some((vec![0.0; out_h * out_w], out_h, out_w));
                            }
                            if let Some((ref mut frame, _, _)) = last_output_frame {
                                for &dst_index in dest_indices {
                                    frame[dst_index] += 1.0;
                                }
                            }
                        }
                    }
                }
            }
        }

        self.last_output_frame = last_output_frame;
        delivered
    }

    fn end_tick_all_layers(&mut self) {
        for layer in &mut self.layers {
            layer.end_tick();
        }
    }

    /// Region growth after end-of-tick: OR-trigger of avg slots or % at cap+fallback; one growth per region per tick.
    fn maybe_grow_region(&mut self) -> Option<usize> {
        if self.layers.len() >= self.growth_policy.max_layers { return None; }
        let current_step = self.layers.get(0).map(|l| l.bus.current_step).unwrap_or(0);
        if current_step.saturating_sub(self.last_layer_growth_step) < self.growth_policy.layer_cooldown_ticks {
            return None;
        }

        // Compute avg slots per neuron and % at cap+fallback
        let mut total_slots: usize = 0;
        let mut total_neurons: usize = 0;
        let mut at_cap_and_fallback: usize = 0;
        let mut saturated_layer_index: Option<usize> = None;
        let mut max_layer_pressure: f64 = -1.0;

        for (layer_index, layer) in self.layers.iter().enumerate() {
            let mut layer_slots: usize = 0;
            let mut layer_neurons: usize = 0;
            let mut layer_at_cap_fallback: usize = 0;
            for neuron in layer.neurons.iter() {
                layer_slots += neuron.slot_engine.slots_len();
                layer_neurons += 1;
                if neuron.slot_engine.is_at_capacity() && neuron.last_slot_used_fallback {
                    layer_at_cap_fallback += 1;
                }
            }
            total_slots += layer_slots;
            total_neurons += layer_neurons;
            let layer_pressure = if layer_neurons == 0 { 0.0 } else { (layer_at_cap_fallback as f64) / (layer_neurons as f64) };
            if layer_pressure > max_layer_pressure {
                max_layer_pressure = layer_pressure;
                saturated_layer_index = Some(layer_index);
            }
            at_cap_and_fallback += layer_at_cap_fallback;
        }

        let avg_slots = if total_neurons == 0 { 0.0 } else { (total_slots as f64) / (total_neurons as f64) };
        let percent_at_cap_fallback = if total_neurons == 0 { 0.0 } else { (at_cap_and_fallback as f64) / (total_neurons as f64) };

        let trigger_by_avg = avg_slots >= self.growth_policy.avg_slots_threshold;
        let trigger_by_percent = percent_at_cap_fallback >= self.growth_policy.percent_at_cap_fallback_threshold;

        if trigger_by_avg || trigger_by_percent {
            if let Some(seed_layer_index) = saturated_layer_index {
                // Add spillover layer (excitatory-only) with same decay & domain
                let decay = self.layers[seed_layer_index].bus.decay_factor;
                let domain = self.layers[seed_layer_index].domain;
                let new_layer_index = match self.layers[seed_layer_index].two_d_shape {
                    Some((h, w)) => {
                        let idx = self.add_output_layer_2d(h, w, decay);
                        idx
                    }
                    None => {
                        self.add_generic_layer(decay, domain)
                    }
                };
                // Record deterministic cross-layer connection with p=1.0
                self.connect_layers(seed_layer_index, new_layer_index, 1.0, false);
                self.last_layer_growth_step = current_step;
                return Some(new_layer_index);
            }
        }
        None
    }

    pub fn tick_2d(&mut self, image: &[f64], height: usize, width: usize) -> RegionMetrics {
        // Phase A
        let fired = self.phase_a_input_2d(image, height, width);
        // Phase B
        let delivered = self.phase_b_propagate(&fired);
        // End tick: end_tick then bus.decay
        self.end_tick_all_layers();
        // Region growth after decay
        let _maybe_layer = self.maybe_grow_region();

        // Metrics
        let mut metrics = RegionMetrics::default();
        metrics.delivered_events = delivered;
        let mut total_slots: usize = 0;
        for layer in &self.layers {
            for neuron in &layer.neurons {
                total_slots += neuron.slot_engine.slots_len();
            }
        }
        metrics.total_slots = total_slots;

        // Count synapses: sum of dest_to_sources lengths across tracts
        let mut total_synapses: usize = 0;
        for tract in &self.tracts {
            for sources in tract.mapping.dest_to_sources.iter() {
                total_synapses += sources.len();
            }
        }
        metrics.total_synapses = total_synapses;

        // Spatial metrics
        if self.spatial_metrics_enabled {
            if let Some((ref output_frame, out_h, out_w)) = self.last_output_frame {
                let spatial = compute_spatial_metrics_from_frame(output_frame, *out_h, *out_w);
                if spatial.active_count > 0 {
                    metrics.spatial = Some(spatial);
                } else {
                    let spatial = compute_spatial_metrics_from_frame(image, height, width);
                    metrics.spatial = Some(spatial);
                }
            } else {
                let spatial = compute_spatial_metrics_from_frame(image, height, width);
                metrics.spatial = Some(spatial);
            }
        }

        metrics
    }
}

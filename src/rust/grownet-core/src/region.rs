use crate::bus::LateralBus;
use crate::ids::{LayerId};
use crate::layer::Layer;
use crate::mesh::MeshRule;
use crate::rng::DeterministicRng;
use crate::slot_config::SlotConfig;
use crate::slot_engine::SlotDomain;
use crate::neuron::NeuronKind;
use crate::tract::Tract;

#[derive(Clone, Debug)]
pub struct GrowthPolicy {
    pub avg_slots_threshold: f64,
    pub percent_at_cap_fallback_threshold: f64,
    pub max_layers: usize,
    pub layer_cooldown_ticks: u64,
}

impl Default for GrowthPolicy {
    fn default() -> Self {
        Self {
            avg_slots_threshold: f64::INFINITY, // off by default
            percent_at_cap_fallback_threshold: 1.1, // >100% off
            max_layers: usize::MAX,
            layer_cooldown_ticks: 500,
        }
    }
}

#[derive(Debug)]
pub struct Region {
    pub layers: Vec<Layer>,
    pub mesh_rules: Vec<MeshRule>,
    pub tracts: Vec<Tract>,
    pub rng: DeterministicRng,
    pub growth_policy: GrowthPolicy,
    pub last_layer_growth_step: u64,
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
        }
    }

    pub fn add_layer(&mut self, decay_factor: f64, domain: SlotDomain) -> usize {
        let id = LayerId(self.layers.len() as u32);
        let layer = Layer::new(id, decay_factor, domain);
        self.layers.push(layer);
        self.layers.len() - 1
    }

    /// Deterministic spillover wiring (p=1.0 by default)
    pub fn connect_layers(&mut self, src: usize, dst: usize, probability: f64, feedback: bool) {
        let rule = MeshRule {
            src: self.layers[src].id,
            dst: self.layers[dst].id,
            probability,
            feedback,
        };
        self.mesh_rules.push(rule);
    }

    /// Windowed connection scaffold returning unique source subscriptions.
    /// Uses the "center" rule for SAME/VALID mapping (Phase 1 stub).
    pub fn connect_layers_windowed(&mut self, _src: usize, _dst: usize, unique_sources: usize) -> usize {
        let tract = Tract::new(unique_sources);
        self.tracts.push(tract);
        self.tracts.len() - 1
    }

    pub fn request_layer_growth(&mut self, saturated_layer_index: usize) -> Option<usize> {
        if self.layers.len() >= self.growth_policy.max_layers {
            return None;
        }
        // Enforce one growth per region per tick via cooldown against bus step
        let current_step = self.layers.get(0).map(|l| l.bus.current_step).unwrap_or(0);
        if current_step.saturating_sub(self.last_layer_growth_step) < self.growth_policy.layer_cooldown_ticks {
            return None;
        }
        // Add small spillover layer (excitatory-only)
        let new_index = self.add_layer(self.layers[saturated_layer_index].bus.decay_factor, self.layers[saturated_layer_index].domain);
        // wire saturated -> new with p=1.0
        self.connect_layers(saturated_layer_index, new_index, 1.0, false);
        self.last_layer_growth_step = current_step;
        Some(new_index)
    }

    /// Two-phase tick scaffold for 2D input.
    pub fn tick_2d(&mut self) {
        // Phase A: integrate/select/reinforce; omitted in Phase 1
        // Phase B: events propagate; tracts could observe; omitted in Phase 1

        // end_tick: per-layer neuron.end_tick(); then bus.decay()
        for layer in &mut self.layers {
            layer.end_tick();
        }
    }

    /// Helper to seed a simple input layer with a few neurons for tests/demos.
    pub fn seed_simple_layer(&mut self, layer_index: usize, neuron_count: usize, cfg: SlotConfig) {
        let layer = &mut self.layers[layer_index];
        for _ in 0..neuron_count {
            layer.push_neuron(NeuronKind::Excitatory, cfg.clone());
        }
    }
}

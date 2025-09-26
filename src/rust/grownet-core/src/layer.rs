use crate::bus::LateralBus;
use crate::ids::{LayerId, NeuronId};
use crate::neuron::{Neuron, NeuronKind};
use crate::slot_config::SlotConfig;
use crate::slot_engine::SlotDomain;

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum LayerKind { Generic, Input2D, Output2D }

#[derive(Debug)]
pub struct Layer {
    pub id: LayerId,
    pub kind: LayerKind,
    pub neurons: Vec<Neuron>,
    pub bus: LateralBus,
    pub domain: SlotDomain,
    pub two_d_shape: Option<(usize, usize)>, // (height, width) when domain == TwoD
}

impl Layer {
    pub fn new_generic(id: LayerId, decay_factor: f64, domain: SlotDomain) -> Self {
        Self { id, kind: LayerKind::Generic, neurons: Vec::new(), bus: LateralBus::new(decay_factor), domain, two_d_shape: None }
    }

    pub fn new_2d(id: LayerId, kind: LayerKind, decay_factor: f64, height: usize, width: usize) -> Self {
        Self { id, kind, neurons: Vec::new(), bus: LateralBus::new(decay_factor), domain: SlotDomain::TwoD, two_d_shape: Some((height, width)) }
    }

    pub fn add_neuron_same_kind(&mut self, seed_index: usize) -> usize {
        let seed = &self.neurons[seed_index];
        let new_id = NeuronId(self.neurons.len() as u32);
        let new_neuron = Neuron::new(new_id, seed.kind, seed.slot_cfg.clone(), self.domain);
        self.neurons.push(new_neuron);
        self.neurons.len() - 1
    }

    pub fn push_neuron(&mut self, kind: NeuronKind, slot_cfg: SlotConfig) -> usize {
        let id = NeuronId(self.neurons.len() as u32);
        let neuron = Neuron::new(id, kind, slot_cfg, self.domain);
        self.neurons.push(neuron);
        self.neurons.len() - 1
    }

    pub fn end_tick_and_maybe_grow(&mut self) -> Option<usize> {
        for neuron in &mut self.neurons {
            neuron.end_tick();
        }
        // Growth escalation: per-layer at most one neuron per tick
        let current_step = self.bus.current_step;
        for index in 0..self.neurons.len() {
            let neuron = &self.neurons[index];
            if neuron.slot_cfg.neuron_growth_enabled
                && neuron.fallback_streak >= neuron.slot_cfg.fallback_growth_threshold
                && current_step.saturating_sub(neuron.last_growth_step) >= neuron.slot_cfg.neuron_growth_cooldown_ticks
            {
                let new_index = self.add_neuron_same_kind(index);
                // Reset streak and set growth step
                let neuron_mut = &mut self.neurons[index];
                neuron_mut.fallback_streak = 0;
                neuron_mut.last_growth_step = current_step;
                return Some(new_index);
            }
        }
        None
    }

    pub fn end_tick(&mut self) {
        self.end_tick_and_maybe_grow();
        self.bus.decay();
    }

    pub fn grid_index_to_row_col(&self, neuron_index: usize) -> Option<(usize, usize)> {
        self.two_d_shape.map(|(height, width)| (neuron_index / width, neuron_index % width))
    }
}

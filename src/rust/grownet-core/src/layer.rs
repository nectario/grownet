use crate::bus::LateralBus;
use crate::ids::{LayerId, NeuronId};
use crate::neuron::{Neuron, NeuronKind};
use crate::slot_config::SlotConfig;
use crate::slot_engine::SlotDomain;

#[derive(Debug)]
pub struct Layer {
    pub id: LayerId,
    pub neurons: Vec<Neuron>,
    pub bus: LateralBus,
    pub domain: SlotDomain,
}

impl Layer {
    pub fn new(id: LayerId, decay_factor: f64, domain: SlotDomain) -> Self {
        Self {
            id,
            neurons: Vec::new(),
            bus: LateralBus::new(decay_factor),
            domain,
        }
    }

    pub fn add_neuron_same_kind(&mut self, seed_index: usize) -> usize {
        let seed = &self.neurons[seed_index];
        let new_id = NeuronId(self.neurons.len() as u32);
        let mut cfg_clone = seed.slot_cfg.clone();
        // Keep the same limits and binning
        let new_neuron = Neuron::new(new_id, seed.kind, cfg_clone, self.domain);
        self.neurons.push(new_neuron);
        self.neurons.len() - 1
    }

    pub fn push_neuron(&mut self, kind: NeuronKind, slot_cfg: SlotConfig) -> usize {
        let id = NeuronId(self.neurons.len() as u32);
        let neuron = Neuron::new(id, kind, slot_cfg, self.domain);
        self.neurons.push(neuron);
        self.neurons.len() - 1
    }

    pub fn end_tick(&mut self) {
        for neuron in &mut self.neurons {
            neuron.end_tick(&mut self.bus);
        }
        self.bus.decay();
    }
}

use crate::bus::LateralBus;
use crate::slot_config::SlotConfig;
use crate::slot_engine::{SlotEngine, SlotDomain};
use crate::ids::{NeuronId, SlotId};

#[derive(Copy, Clone, Debug)]
pub enum NeuronKind {
    Excitatory,
    Inhibitory,
    Modulatory,
}

#[derive(Debug)]
pub struct Neuron {
    pub id: NeuronId,
    pub kind: NeuronKind,
    pub slot_cfg: SlotConfig,
    pub slot_engine: SlotEngine,
    pub last_slot_used_fallback: bool,
    pub fallback_streak: u32,
    pub last_growth_step: u64,
}

impl Neuron {
    pub fn new(id: NeuronId, kind: NeuronKind, slot_cfg: SlotConfig, domain: SlotDomain) -> Self {
        let capacity = slot_cfg.slot_limit;
        let engine = match domain {
            SlotDomain::Scalar => SlotEngine::new_scalar(capacity, slot_cfg.bin_width_pct, slot_cfg.epsilon_scale),
            SlotDomain::TwoD => SlotEngine::new_two_d(capacity, slot_cfg.bin_width_pct, slot_cfg.epsilon_scale),
        };
        Self {
            id,
            kind,
            slot_cfg,
            slot_engine: engine,
            last_slot_used_fallback: false,
            fallback_streak: 0,
            last_growth_step: 0,
        }
    }

    pub fn observe_scalar(&mut self, value: f64) -> SlotId {
        let selection = self.slot_engine.observe_scalar(value);
        self.last_slot_used_fallback = selection.used_fallback;
        if self.last_slot_used_fallback {
            self.fallback_streak = self.fallback_streak.saturating_add(1);
        } else {
            self.fallback_streak = 0;
        }
        selection.slot_id
    }

    pub fn observe_two_d(&mut self, row: f64, col: f64) -> SlotId {
        let selection = self.slot_engine.observe_two_d(row, col);
        self.last_slot_used_fallback = selection.used_fallback;
        if self.last_slot_used_fallback {
            self.fallback_streak = self.fallback_streak.saturating_add(1);
        } else {
            self.fallback_streak = 0;
        }
        selection.slot_id
    }

    pub fn end_tick(&mut self, _bus: &mut LateralBus) {
        // In Phase-B propagation we would accumulate effects;
        // end_tick hook available for decay of per-neuron state if needed.
    }
}

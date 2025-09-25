//! Proximity connectivity policy (Phase 1 scaffold).

use grownet_core::ids::LayerId;

#[derive(Clone, Debug)]
pub enum ProbabilityMode { Step, Linear, Logistic }

#[derive(Clone, Debug)]
pub struct ProximityConfig {
    pub radius: f64,
    pub budget_per_tick: usize,
    pub per_source_cooldown: u64,
    pub probability_mode: ProbabilityMode,
}

#[derive(Clone, Debug)]
pub struct SlotConfig {
    pub slot_limit: usize,
    pub bin_width_pct: f64, // for scalar or row/col if using TwoD with same width
    pub epsilon_scale: f64,
    pub fallback_growth_threshold: u32,
    pub neuron_growth_cooldown_ticks: u64,
    pub growth_enabled: bool,
    pub neuron_growth_enabled: bool,
    pub layer_growth_enabled: bool,
}

impl Default for SlotConfig {
    fn default() -> Self {
        Self {
            slot_limit: 8,
            bin_width_pct: 5.0,
            epsilon_scale: 1e-6,
            fallback_growth_threshold: 3,
            neuron_growth_cooldown_ticks: 0,
            growth_enabled: true,
            neuron_growth_enabled: true,
            layer_growth_enabled: false,
        }
    }
}

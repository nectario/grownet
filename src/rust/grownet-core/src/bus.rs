#[derive(Clone, Debug)]
pub struct LateralBus {
    pub inhibition: f64,
    pub modulation: f64,
    pub current_step: u64,
    pub decay_factor: f64,
}

impl LateralBus {
    pub fn new(decay_factor: f64) -> Self {
        Self { inhibition: 0.0, modulation: 1.0, current_step: 0, decay_factor }
    }

    /// End-of-tick decay: inhibition decays multiplicatively; modulation resets;
    /// and current_step increments by one.
    pub fn decay(&mut self) {
        self.inhibition *= self.decay_factor;
        self.modulation = 1.0;
        self.current_step = self.current_step.saturating_add(1);
    }
}

use crate::ids::NeuronId;

#[derive(Clone, Debug)]
pub struct Tract {
    /// unique source subscriptions count per window (center rule)
    pub unique_sources: usize,
    // Additional window mapping and attachment state can be added here.
}

impl Tract {
    pub fn new(unique_sources: usize) -> Self {
        Self { unique_sources }
    }

    pub fn attach_source_neuron(&mut self, _new_index: usize) {
        // Re-attach logic would extend internal mappings to include the grown source neuron.
        // Left as Phase 1 scaffold.
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
pub struct LayerId(pub u32);

#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
pub struct NeuronId(pub u32);

#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
pub struct SlotId(pub u32);

impl SlotId {
    pub const FALLBACK: SlotId = SlotId(u32::MAX);
}

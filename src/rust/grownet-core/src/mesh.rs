use crate::ids::LayerId;

#[derive(Clone, Debug)]
pub struct MeshRule {
    pub src: LayerId,
    pub dst: LayerId,
    pub probability: f64, // deterministic p=1.0 in default spillover
    pub feedback: bool,
}

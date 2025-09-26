use crate::ids::LayerId;

#[derive(Clone, Debug)]
pub struct MeshRule {
    pub src: LayerId,
    pub dst: LayerId,
    pub probability: f64,
    pub feedback: bool,
}

//! GrowNet Core — Rust (Phase 2)
pub mod ids;
pub mod rng;
pub mod bus;
pub mod slot_config;
pub mod slot_engine;
pub mod neuron;
pub mod layer;
pub mod mesh;
pub mod window;
pub mod tract;
pub mod spatial_metrics;
pub mod region;

#[cfg(test)]
mod tests;

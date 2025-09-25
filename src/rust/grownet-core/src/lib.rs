//! GrowNet Core — Rust (Phase 1)
//!
//! Core hierarchy and invariants with deterministic behavior.

pub mod ids;
pub mod rng;
pub mod bus;
pub mod slot_config;
pub mod slot_engine;
pub mod neuron;
pub mod layer;
pub mod mesh;
pub mod tract;
pub mod region;

#[cfg(test)]
mod tests;

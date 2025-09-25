use crate::bus::LateralBus;
use crate::slot_engine::SlotEngine;
use crate::slot_engine::SlotDomain;
use crate::slot_config::SlotConfig;
use crate::region::Region;

#[test]
fn bus_decay_parity() {
    let mut bus = LateralBus::new(0.9);
    bus.inhibition = 10.0;
    bus.modulation = 0.3;
    let before_step = bus.current_step;
    bus.decay();
    assert!((bus.inhibition - 9.0).abs() < 1e-9);
    assert!((bus.modulation - 1.0).abs() < 1e-12);
    assert_eq!(bus.current_step, before_step + 1);
}

#[test]
fn slot_engine_scalar_capacity_and_fallback() {
    let mut engine = SlotEngine::new_scalar(2, 5.0, 1e-6);
    let s1 = engine.observe_scalar(10.0); // anchor set
    assert!(!engine.last_slot_used_fallback);
    let s2 = engine.observe_scalar(10.5);
    assert!(!engine.last_slot_used_fallback);
    let s3 = engine.observe_scalar(11.0);
    // capacity reached: expect fallback on a third distinct bin
    assert!(engine.last_slot_used_fallback);
    assert_eq!(s3.slot_id, crate::ids::SlotId::FALLBACK);
}

#[test]
fn prefer_last_slot_once_semantics() {
    let mut engine = SlotEngine::new_scalar(1, 1.0, 1e-6);
    let _ = engine.observe_scalar(100.0);
    engine.freeze_last_slot();
    engine.unfreeze_last_slot();
    let next = engine.observe_scalar(103.0);
    assert_eq!(engine.last_slot_used_fallback, false);
    // After one-shot reuse, a new different bin should fallback due to cap
    let next2 = engine.observe_scalar(110.0);
    assert!(engine.last_slot_used_fallback);
}

#[test]
fn one_growth_per_region_per_tick_guard() {
    let mut region = Region::new(1234);
    let l0 = region.add_layer(0.9, SlotDomain::Scalar);
    let cfg = SlotConfig { slot_limit: 1, ..Default::default() };
    region.seed_simple_layer(l0, 1, cfg);
    // Cooldown default is 500; initial last_layer_growth_step = 0; current step = 0
    // First request should succeed
    let first = region.request_layer_growth(0);
    assert!(first.is_some());
    // Same tick: second should be rejected
    let second = region.request_layer_growth(0);
    assert!(second.is_none());
}

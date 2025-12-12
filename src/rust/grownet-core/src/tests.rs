use crate::bus::LateralBus;
use crate::slot_engine::SlotEngine;
use crate::slot_engine::SlotDomain;
use crate::slot_config::SlotConfig;
use crate::region::{Region, GrowthPolicy};
use crate::window::{compute_window_mapping, Padding};

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
    let _s1 = engine.observe_scalar(10.0); // anchor set
    assert!(!engine.last_slot_used_fallback);
    let _s2 = engine.observe_scalar(10.5);
    assert!(!engine.last_slot_used_fallback);
    let _s3 = engine.observe_scalar(11.0);
    assert!(engine.last_slot_used_fallback);
}

#[test]
fn window_mapping_same_center_rule() {
    let map = compute_window_mapping(5, 5, 3, 3, 1, 1, Padding::Same);
    // out dims equal to input for SAME with stride 1
    assert_eq!(map.out_height, 5);
    assert_eq!(map.out_width, 5);
    // unique sources should be <= 25
    assert!(map.unique_source_count <= 25);
}

#[test]
fn region_tick_2d_delivered_and_metrics() {
    let mut region = Region::new(1234);
    let src = region.add_input_layer_2d(4, 4, 0.95);
    let dst = region.add_output_layer_2d(4, 4, 0.95);
    // Connect with 3x3 SAME window
    let unique_sources = region.connect_layers_windowed(src, dst, 3, 3, 1, 1, Padding::Same);
    assert!(unique_sources > 0);

    let frame: Vec<f64> = vec![0.0; 16];
    let mut frame_active = frame.clone();
    frame_active[5] = 1.0; // one active pixel

    let metrics = region.tick_2d(&frame_active, 4, 4);
    assert!(metrics.delivered_events > 0);
    assert!(metrics.total_synapses > 0);
    assert!(metrics.spatial.is_some());
}

#[test]
fn neuron_growth_on_fallback_streak() {
    let mut region = Region::new(1234);
    let src = region.add_input_layer_2d(2, 2, 0.95);
    region.seed_simple_layer(src, 1, SlotConfig { slot_limit: 1, fallback_growth_threshold: 2, neuron_growth_cooldown_ticks: 0, ..Default::default() });
    // Create repeated fallback: with slot_limit=1 and changing bins
    let frame1 = vec![1.0, 2.0, 3.0, 4.0];
    let _m1 = region.tick_2d(&frame1, 2, 2);
    let frame2 = vec![10.0, 20.0, 30.0, 40.0];
    let _m2 = region.tick_2d(&frame2, 2, 2);
    // After two consecutive fallbacks, one growth in that layer should have happened (end_tick escalation)
    assert!(region.layers[src].neurons.len() >= 2);
}

#[test]
fn region_growth_or_trigger() {
    let mut region = Region::new(1234);
    let src = region.add_input_layer_2d(3, 3, 0.95);
    // Seed enough neurons with small capacity to push avg slots up
    region.seed_simple_layer(src, 4, SlotConfig { slot_limit: 1, ..Default::default() });
    // Aggressive policy
    region.growth_policy = GrowthPolicy { avg_slots_threshold: 0.5, percent_at_cap_fallback_threshold: 0.0, max_layers: 64, layer_cooldown_ticks: 0 };
    let frame = vec![1.0; 9];
    let _m = region.tick_2d(&frame, 3, 3);
    // Should have added at least one layer via region growth
    assert!(region.layers.len() >= 2);
}

#[test]
fn region_one_growth_per_tick() {
    let mut region = Region::new(1234);
    let src = region.add_input_layer_2d(4, 4, 0.95);
    let dst = region.add_output_layer_2d(4, 4, 0.95);
    region.connect_layers_windowed(src, dst, 3, 3, 1, 1, Padding::Same);

    region.growth_policy = GrowthPolicy {
        avg_slots_threshold: 0.0,
        percent_at_cap_fallback_threshold: 2.0, // off
        max_layers: 64,
        layer_cooldown_ticks: 0,
    };

    let frame = vec![1.0; 16];
    let mut prev_layer_count = region.layers.len();
    for _ in 0..5 {
        let metrics = region.tick_2d(&frame, 4, 4);
        assert!(metrics.delivered_events > 0);
        let now_layer_count = region.layers.len();
        assert!(now_layer_count >= prev_layer_count);
        assert!(now_layer_count - prev_layer_count <= 1);
        prev_layer_count = now_layer_count;
    }
}

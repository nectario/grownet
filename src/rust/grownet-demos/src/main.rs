use grownet_core::region::Region;
use grownet_core::slot_engine::SlotDomain;
use grownet_core::slot_config::SlotConfig;

fn main() {
    let mut region = Region::new(1234);
    let layer_index = region.add_layer(0.92, SlotDomain::Scalar);
    region.seed_simple_layer(layer_index, 3, SlotConfig::default());
    // Run a few ticks (no IO in Phase 1)
    for _ in 0..5 {
        region.tick_2d();
    }
    println!("GrowNet Rust Phase 1 ready: layers = {}", region.layers.len());
}

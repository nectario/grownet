use grownet_core::region::Region;
use grownet_core::window::Padding;

fn main() {
    let mut region = Region::new(1234);
    let src = region.add_input_layer_2d(8, 8, 0.92);
    let dst = region.add_output_layer_2d(8, 8, 0.92);
    let unique_sources = region.connect_layers_windowed(src, dst, 5, 5, 2, 2, Padding::Same);
    println!("Unique sources: {}", unique_sources);

    // Activate a small blob
    let mut frame: Vec<f64> = vec![0.0; 64];
    frame[27] = 1.0;
    frame[28] = 1.0;
    let metrics = region.tick_2d(&frame, 8, 8);
    println!("Delivered events: {}", metrics.delivered_events);
    println!("Total slots: {}", metrics.total_slots);
    println!("Total synapses: {}", metrics.total_synapses);
    if let Some(spatial) = metrics.spatial {
        println!("Spatial active={} bbox=({},{})->({},{}), centroid=({:.2},{:.2})",
            spatial.active_count, spatial.min_row, spatial.min_col, spatial.max_row, spatial.max_col,
            spatial.centroid_row, spatial.centroid_col);
    }
}

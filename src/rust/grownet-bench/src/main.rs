use grownet_core::region::Region;
use grownet_core::window::Padding;
use serde::Serialize;
use std::collections::HashMap;
use std::time::Instant;

#[derive(Serialize)]
struct Output {
    impl_: &'static str,
    scenario: String,
    runs: u32,
    metrics: serde_json::Value,
}

fn parse_args() -> HashMap<String, String> {
    let mut m = HashMap::new();
    let mut i = 1usize;
    let args: Vec<String> = std::env::args().collect();
    while i < args.len() {
        let a = &args[i];
        if a == "--scenario" && i + 1 < args.len() { m.insert("scenario".into(), args[i + 1].clone()); i += 1; }
        else if a == "--json" { m.insert("json".into(), "1".into()); }
        else if a == "--params" && i + 1 < args.len() { m.insert("params".into(), args[i + 1].clone()); i += 1; }
        i += 1;
    }
    m
}

fn bench_image(params: &serde_json::Value) -> serde_json::Value {
    let height = params.get("height").and_then(|v| v.as_u64()).unwrap_or(64) as usize;
    let width = params.get("width").and_then(|v| v.as_u64()).unwrap_or(64) as usize;
    let frames = params.get("frames").and_then(|v| v.as_u64()).unwrap_or(100) as usize;

    let mut region = Region::new(1234);
    let src = region.add_input_layer_2d(height, width, 0.92);
    let dst = region.add_output_layer_2d(height, width, 0.20);
    let _unique = region.connect_layers_windowed(src, dst, 3, 3, 1, 1, Padding::Same);

    let mut rng: u64 = 123456789;
    let mut make_frame = || {
        let mut v = vec![0f64; height * width];
        for idx in 0..v.len() {
            // xorshift32
            rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
            v[idx] = ((rng & 0xffff) as f64) / 65535.0;
        }
        v
    };

    // Warmup
    let f0 = make_frame();
    let _m0 = region.tick_2d(&f0, height, width);

    let t0 = Instant::now();
    let mut delivered: u64 = 0;
    for _ in 0..frames {
        let f = make_frame();
        let m = region.tick_2d(&f, height, width);
        delivered += m.delivered_events;
    }
    let elapsed = t0.elapsed();
    let total_ms = elapsed.as_secs_f64() * 1000.0;
    serde_json::json!({
        "e2e_wall_ms": total_ms,
        "ticks": frames,
        "per_tick_us_avg": (total_ms * 1000.0) / (frames as f64),
        "delivered_events": delivered,
    })
}

fn bench_scalar(params: &serde_json::Value) -> serde_json::Value {
    // Simulate scalar via 1x1 2D ticks
    let ticks = params.get("ticks").and_then(|v| v.as_u64()).unwrap_or(50_000) as usize;
    let mut region = Region::new(1234);
    let _src = region.add_input_layer_2d(1, 1, 0.92);
    let frame = vec![0.42f64; 1];
    // Warmup
    let _ = region.tick_2d(&frame, 1, 1);
    let t0 = Instant::now();
    for _ in 0..ticks { let _ = region.tick_2d(&frame, 1, 1); }
    let elapsed = t0.elapsed();
    let total_ms = elapsed.as_secs_f64() * 1000.0;
    serde_json::json!({
        "e2e_wall_ms": total_ms,
        "ticks": ticks,
        "per_tick_us_avg": (total_ms * 1000.0) / (ticks as f64),
    })
}

fn main() {
    let args_map = parse_args();
    let scenario = args_map.get("scenario").cloned().unwrap_or_else(|| "image_64x64".into());
    let params_val: serde_json::Value = args_map
        .get("params")
        .and_then(|s| serde_json::from_str::<serde_json::Value>(s).ok())
        .unwrap_or_else(|| serde_json::json!({}));

    let metrics = match scenario.as_str() {
        "scalar_small" => bench_scalar(&params_val),
        _ => bench_image(&params_val),
    };

    let out = Output { impl_: "rust", scenario, runs: 1, metrics };
    // Emit one JSON line
    let json = serde_json::to_string(&serde_json::json!({
        "impl": out.impl_,
        "scenario": out.scenario,
        "runs": out.runs,
        "metrics": out.metrics,
    })).unwrap();
    println!("{}", json);
}


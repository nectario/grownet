from region import Region
from topographic_wiring import TopographicConfig, connect_layers_topographic

fn main() -> None:
    var region = Region("topo-demo")
    var src = region.add_input_layer_2d(16, 16, 1.0, 0.01)
    var dst = region.add_output_layer_2d(16, 16, 0.0)
    var cfg = TopographicConfig()
    cfg.kernel_h = 7; cfg.kernel_w = 7
    cfg.padding = "same"
    cfg.weight_mode = "gaussian"
    cfg.sigma_center = 2.0
    cfg.normalize_incoming = True
    var unique_sources = connect_layers_topographic(region, src, dst, cfg)
    print("unique_sources=", unique_sources)

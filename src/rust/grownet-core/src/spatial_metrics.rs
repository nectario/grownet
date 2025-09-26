#[derive(Clone, Debug, Default)]
pub struct SpatialMetrics {
    pub min_row: usize,
    pub max_row: usize,
    pub min_col: usize,
    pub max_col: usize,
    pub centroid_row: f64,
    pub centroid_col: f64,
    pub active_count: usize,
}

pub fn compute_spatial_metrics_from_frame(frame: &[f64], height: usize, width: usize) -> SpatialMetrics {
    let mut metrics = SpatialMetrics::default();
    let mut sum_row: f64 = 0.0;
    let mut sum_col: f64 = 0.0;
    let mut min_row = usize::MAX;
    let mut min_col = usize::MAX;
    let mut max_row = 0usize;
    let mut max_col = 0usize;
    let mut active_count: usize = 0;

    for row in 0..height {
        for col in 0..width {
            let value = frame[row * width + col];
            if value != 0.0 {
                active_count += 1;
                sum_row += row as f64;
                sum_col += col as f64;
                if row < min_row { min_row = row; }
                if col < min_col { min_col = col; }
                if row > max_row { max_row = row; }
                if col > max_col { max_col = col; }
            }
        }
    }

    if active_count == 0 {
        return metrics; // zeros; centroid remains 0
    }

    metrics.min_row = min_row;
    metrics.min_col = min_col;
    metrics.max_row = max_row;
    metrics.max_col = max_col;
    metrics.centroid_row = sum_row / (active_count as f64);
    metrics.centroid_col = sum_col / (active_count as f64);
    metrics.active_count = active_count;
    metrics
}

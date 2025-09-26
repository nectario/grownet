use hashbrown::{HashSet, HashMap};

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum Padding { Same, Valid }

#[derive(Debug)]
pub struct WindowMapping {
    pub out_height: usize,
    pub out_width: usize,
    /// For each destination index (row-major), store list of unique source indices
    pub dest_to_sources: Vec<Vec<usize>>,
    /// Reverse index for fast propagation: for each source index, the set of dest indices
    pub source_to_dests: HashMap<usize, Vec<usize>>,
    pub unique_source_count: usize,
}

fn output_dim_same(input_dim: usize, stride: usize) -> usize {
    ((input_dim as f64) / (stride as f64)).ceil() as usize
}

fn output_dim_valid(input_dim: usize, kernel: usize, stride: usize) -> usize {
    if input_dim < kernel { 0 } else { 1 + (input_dim - kernel) / stride }
}

pub fn compute_window_mapping(
    source_height: usize, source_width: usize,
    kernel_height: usize, kernel_width: usize,
    stride_height: usize, stride_width: usize,
    padding: Padding
) -> WindowMapping {
    let (out_h, out_w) = match padding {
        Padding::Same => (output_dim_same(source_height, stride_height),
                          output_dim_same(source_width, stride_width)),
        Padding::Valid => (output_dim_valid(source_height, kernel_height, stride_height),
                           output_dim_valid(source_width, kernel_width, stride_width)),
    };
    let mut dest_to_sources: Vec<Vec<usize>> = vec![Vec::new(); out_h * out_w];
    let mut union_sources: HashSet<usize> = HashSet::new();

    let half_kh = (kernel_height as isize) / 2;
    let half_kw = (kernel_width as isize) / 2;

    for dest_row in 0..out_h {
        for dest_col in 0..out_w {
            let center_row_estimate = (dest_row * stride_height) as isize;
            let center_col_estimate = (dest_col * stride_width) as isize;
            // SAME: clamp centers into image; VALID: ensure window fully in-bounds by clamping edges
            let center_row = match padding {
                Padding::Same => center_row_estimate.clamp(0, (source_height as isize) - 1),
                Padding::Valid => center_row_estimate + half_kh,
            };
            let center_col = match padding {
                Padding::Same => center_col_estimate.clamp(0, (source_width as isize) - 1),
                Padding::Valid => center_col_estimate + half_kw,
            };
            let start_row = (center_row - half_kh).max(0) as usize;
            let end_row = ((center_row + half_kh) as isize).min((source_height as isize) - 1) as usize;
            let start_col = (center_col - half_kw).max(0) as usize;
            let end_col = ((center_col + half_kw) as isize).min((source_width as isize) - 1) as usize;

            let dest_index = dest_row * out_w + dest_col;
            let mut local_set: HashSet<usize> = HashSet::new();
            for row in start_row..=end_row {
                for col in start_col..=end_col {
                    let src_index = row * source_width + col;
                    if local_set.insert(src_index) {
                        dest_to_sources[dest_index].push(src_index);
                        union_sources.insert(src_index);
                    }
                }
            }
        }
    }

    // Build reverse mapping
    let mut source_to_dests: HashMap<usize, Vec<usize>> = HashMap::new();
    for (dest_index, src_list) in dest_to_sources.iter().enumerate() {
        for &src in src_list {
            source_to_dests.entry(src).or_default().push(dest_index);
        }
    }

    WindowMapping {
        out_height: out_h,
        out_width: out_w,
        dest_to_sources,
        source_to_dests,
        unique_source_count: union_sources.len(),
    }
}

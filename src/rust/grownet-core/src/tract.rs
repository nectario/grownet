use crate::window::{WindowMapping, Padding, compute_window_mapping};

#[derive(Clone, Debug)]
pub struct Tract {
    pub source_layer_index: usize,
    pub dest_layer_index: usize,
    pub mapping: WindowMapping,
    pub source_height: usize,
    pub source_width: usize,
    pub kernel_height: usize,
    pub kernel_width: usize,
    pub stride_height: usize,
    pub stride_width: usize,
    pub padding: Padding,
}

impl Tract {
    pub fn new(
        source_layer_index: usize, dest_layer_index: usize,
        source_height: usize, source_width: usize,
        kernel_height: usize, kernel_width: usize,
        stride_height: usize, stride_width: usize,
        padding: Padding
    ) -> Self {
        let mapping = compute_window_mapping(source_height, source_width, kernel_height, kernel_width, stride_height, stride_width, padding);
        Self {
            source_layer_index,
            dest_layer_index,
            mapping,
            source_height,
            source_width,
            kernel_height,
            kernel_width,
            stride_height,
            stride_width,
            padding,
        }
    }

    pub fn unique_source_count(&self) -> usize { self.mapping.unique_source_count }

    /// Rebuilds only the reverse indices needed to include a newly added source index.
    /// For 2D grids we detect which dest windows cover the given source index and attach.
    pub fn attach_source_neuron(&mut self, new_source_index: usize) {
        let row = new_source_index / self.source_width;
        let col = new_source_index % self.source_width;

        let half_kh = (self.kernel_height as isize) / 2;
        let half_kw = (self.kernel_width as isize) / 2;

        let mut candidate_dest_indices: Vec<usize> = Vec::new();
        // Iterate all dest windows; for large grids, this could be optimized by range math
        for dest_row in 0..self.mapping.out_height {
            for dest_col in 0..self.mapping.out_width {
                let center_row_estimate = (dest_row * self.stride_height) as isize;
                let center_col_estimate = (dest_col * self.stride_width) as isize;
                let center_row = match self.padding {
                    crate::window::Padding::Same => center_row_estimate.clamp(0, (self.source_height as isize) - 1),
                    crate::window::Padding::Valid => center_row_estimate + half_kh,
                };
                let center_col = match self.padding {
                    crate::window::Padding::Same => center_col_estimate.clamp(0, (self.source_width as isize) - 1),
                    crate::window::Padding::Valid => center_col_estimate + half_kw,
                };
                let start_row = (center_row - half_kh).max(0) as usize;
                let end_row = ((center_row + half_kh) as isize).min((self.source_height as isize) - 1) as usize;
                let start_col = (center_col - half_kw).max(0) as usize;
                let end_col = ((center_col + half_kw) as isize).min((self.source_width as isize) - 1) as usize;

                if row >= start_row && row <= end_row && col >= start_col && col <= end_col {
                    let dest_index = dest_row * self.mapping.out_width + dest_col;
                    candidate_dest_indices.push(dest_index);
                }
            }
        }

        // Update mapping with new subscriptions if missing
        for dest_index in candidate_dest_indices {
            let list = &mut self.mapping.dest_to_sources[dest_index];
            if !list.contains(&new_source_index) {
                list.push(new_source_index);
                self.mapping.source_to_dests.entry(new_source_index).or_default().push(dest_index);
            }
        }
    }
}

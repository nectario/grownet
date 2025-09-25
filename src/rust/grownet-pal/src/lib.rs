//! Deterministic parallelism scaffold (Phase 1: single-threaded).

pub struct ParallelOptions {
    pub max_workers: Option<usize>,
    pub tile_size: Option<usize>,
}

impl Default for ParallelOptions {
    fn default() -> Self {
        Self { max_workers: None, tile_size: None }
    }
}

/// Deterministic parallel_for: executes in submission order.
pub fn parallel_for(start: usize, end: usize, _opts: &ParallelOptions, mut f: impl FnMut(usize)) {
    for index in start..end {
        f(index);
    }
}

/// Deterministic parallel_map with ordered reduction.
pub fn parallel_map<T: Default + Clone>(start: usize, end: usize, _opts: &ParallelOptions, mut f: impl FnMut(usize) -> T, mut reduce: impl FnMut(usize, T)) {
    for index in start..end {
        let value = f(index);
        reduce(index, value);
    }
}

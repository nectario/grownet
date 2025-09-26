//! Deterministic PAL: default single-thread; optional threaded ordered reduction.
use crossbeam_channel as channel;
use std::thread;

#[derive(Clone, Debug, Default)]
pub struct ParallelOptions {
    pub max_workers: Option<usize>,
    pub tile_size: Option<usize>,
}

/// Deterministic single-thread parallel_for.
pub fn parallel_for(start: usize, end: usize, _opts: &ParallelOptions, mut f: impl FnMut(usize)) {
    for index in start..end {
        f(index);
    }
}

/// Threaded ordered parallel_map: tiles the range and reduces results in index order.
pub fn parallel_map_ordered<T: Send + 'static>(
    start: usize, end: usize, opts: &ParallelOptions,
    f: impl Fn(usize) -> T + Send + Sync + 'static,
    mut reduce_in_order: impl FnMut(usize, T)
) {
    let total = end - start;
    if total == 0 { return; }

    let worker_count = opts.max_workers.unwrap_or(1).max(1);
    if worker_count == 1 {
        for index in start..end {
            reduce_in_order(index, f(index));
        }
        return;
    }
    let tile = opts.tile_size.unwrap_or(64).max(1);

    let (tx, rx) = channel::unbounded::<(usize, T)>();
    let f_ref = &f;
    let mut handles = Vec::new();

    // Spawn workers on disjoint tiles
    let mut next = start;
    while next < end {
        let begin = next;
        let finish = (next + tile).min(end);
        next = finish;

        let tx_clone = tx.clone();
        let task = f_ref.clone();
        handles.push(thread::spawn(move || {
            for index in begin..finish {
                let value = task(index);
                tx_clone.send((index, value)).ok();
            }
        }));
    }
    drop(tx);

    // Drain results and apply ordered reduction
    let mut buffer: Vec<Option<T>> = vec![None; total];
    for (index, value) in rx {
        buffer[index - start] = Some(value);
    }
    for offset in 0..total {
        let index = start + offset;
        if let Some(value) = buffer[offset].take() {
            reduce_in_order(index, value);
        }
    }

    for handle in handles {
        let _ = handle.join();
    }
}

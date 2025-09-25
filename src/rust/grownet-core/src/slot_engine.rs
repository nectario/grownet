use std::collections::HashMap;

use crate::ids::SlotId;

#[derive(Clone, Debug)]
pub enum AnchorMode {
    First,
}

#[derive(Copy, Clone, Debug)]
pub enum SlotDomain {
    Scalar,
    TwoD,
}

#[derive(Clone, Debug)]
pub struct SlotEngine {
    domain: SlotDomain,
    anchor_mode: AnchorMode,

    // Anchors per domain
    anchor_set: bool,
    anchor_scalar: f64,
    anchor_row: f64,
    anchor_col: f64,

    // Binning
    bin_width_pct: f64,       // scalar or shared width for TwoD axes
    epsilon_scale: f64,

    // Capacity and slots
    capacity: usize,
    slot_map: HashMap<i64, SlotId>,
    slot_order: Vec<i64>,

    // Flags
    pub last_slot_used_fallback: bool,
    pub prefer_last_slot_once: bool,
    last_slot_id: Option<SlotId>,
    frozen_slot: Option<SlotId>,
}

#[derive(Clone, Debug)]
pub struct SlotSelection {
    pub slot_id: SlotId,
    pub used_fallback: bool,
}

impl SlotEngine {
    pub fn new_scalar(capacity: usize, bin_width_pct: f64, epsilon_scale: f64) -> Self {
        Self {
            domain: SlotDomain::Scalar,
            anchor_mode: AnchorMode::First,
            anchor_set: false,
            anchor_scalar: 0.0,
            anchor_row: 0.0,
            anchor_col: 0.0,
            bin_width_pct,
            epsilon_scale,
            capacity,
            slot_map: HashMap::new(),
            slot_order: Vec::new(),
            last_slot_used_fallback: false,
            prefer_last_slot_once: false,
            last_slot_id: None,
            frozen_slot: None,
        }
    }

    pub fn new_two_d(capacity: usize, bin_width_pct: f64, epsilon_scale: f64) -> Self {
        Self::new_scalar(capacity, bin_width_pct, epsilon_scale).with_two_d()
    }

    fn with_two_d(mut self) -> Self {
        self.domain = SlotDomain::TwoD;
        self
    }

    pub fn domain(&self) -> SlotDomain { self.domain }

    pub fn slots_len(&self) -> usize { self.slot_order.len() }

    fn compute_scalar_bin(&self, value: f64) -> i64 {
        let anchor = self.anchor_scalar;
        let denom = anchor.abs().max(self.epsilon_scale);
        let delta_pct = ((value - anchor).abs() / denom) * 100.0;
        let bin_index = (delta_pct / self.bin_width_pct).floor() as i64;
        bin_index
    }

    fn compute_two_d_bins(&self, row: f64, col: f64) -> (i64, i64) {
        let denom_r = self.anchor_row.abs().max(self.epsilon_scale);
        let denom_c = self.anchor_col.abs().max(self.epsilon_scale);
        let delta_pct_r = ((row - self.anchor_row).abs() / denom_r) * 100.0;
        let delta_pct_c = ((col - self.anchor_col).abs() / denom_c) * 100.0;
        let r_bin = (delta_pct_r / self.bin_width_pct).floor() as i64;
        let c_bin = (delta_pct_c / self.bin_width_pct).floor() as i64;
        (r_bin, c_bin)
    }

    fn pack_two_d_key(r_bin: i64, c_bin: i64) -> i64 {
        // large packing stride; matches docs r*100000 + c
        r_bin * 100_000 + c_bin
    }

    pub fn freeze_last_slot(&mut self) {
        self.frozen_slot = self.last_slot_id;
    }

    pub fn unfreeze_last_slot(&mut self) {
        // one-shot preference to reuse the same slot on next tick
        self.prefer_last_slot_once = true;
    }

    pub fn observe_scalar(&mut self, value: f64) -> SlotSelection {
        if !self.anchor_set {
            self.anchor_set = true;
            self.anchor_scalar = value;
        }
        // one-shot re-preference
        if let Some(slot) = self.frozen_slot {
            if self.prefer_last_slot_once {
                self.prefer_last_slot_once = false;
                self.last_slot_used_fallback = false;
                self.last_slot_id = Some(slot);
                return SlotSelection { slot_id: slot, used_fallback: false };
            }
        }

        let key = self.compute_scalar_bin(value);
        let selection = self.select_or_allocate_slot(key);
        selection
    }

    pub fn observe_two_d(&mut self, row: f64, col: f64) -> SlotSelection {
        if !self.anchor_set {
            self.anchor_set = true;
            self.anchor_row = row;
            self.anchor_col = col;
        }
        if let Some(slot) = self.frozen_slot {
            if self.prefer_last_slot_once {
                self.prefer_last_slot_once = false;
                self.last_slot_used_fallback = false;
                self.last_slot_id = Some(slot);
                return SlotSelection { slot_id: slot, used_fallback: false };
            }
        }
        let (r_bin, c_bin) = self.compute_two_d_bins(row, col);
        let key = Self::pack_two_d_key(r_bin, c_bin);
        let selection = self.select_or_allocate_slot(key);
        selection
    }

    fn select_or_allocate_slot(&mut self, key: i64) -> SlotSelection {
        self.last_slot_used_fallback = false;
        if let Some(slot_id) = self.slot_map.get(&key).copied() {
            self.last_slot_id = Some(slot_id);
            return SlotSelection { slot_id, used_fallback: false };
        }
        // Strict capacity with bootstrap exception if empty
        let can_allocate = if self.slot_order.is_empty() {
            true // bootstrap exception
        } else {
            self.slot_order.len() < self.capacity
        };
        if can_allocate {
            let new_id = SlotId(self.slot_order.len() as u32);
            self.slot_map.insert(key, new_id);
            self.slot_order.push(key);
            self.last_slot_id = Some(new_id);
            SlotSelection { slot_id: new_id, used_fallback: false }
        } else {
            self.last_slot_used_fallback = true;
            self.last_slot_id = Some(SlotId::FALLBACK);
            SlotSelection { slot_id: SlotId::FALLBACK, used_fallback: true }
        }
    }
}

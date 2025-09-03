from slot_config import SlotPolicy
from weight import Weight
from typing import Tuple


class SlotEngine:
    """Slot selection helpers (policy + temporal & spatial focus) with fallback markers."""
    def __init__(self, cfg):
        self.cfg = cfg

    # -------- scalar (temporal) --------
    def slot_id(self, last_input, current_input, known_slots):
        """Map a percent delta to an integer bin (policy-dependent)."""
        if self.cfg.policy == SlotPolicy.FIXED:
            if last_input == 0:
                return 0
            delta_percent = abs(current_input - last_input) / max(1e-9, abs(last_input)) * 100.0
            bin_width = max(1.0, self.cfg.fixed_delta_percent)
            return int(delta_percent // bin_width)
        elif self.cfg.policy == SlotPolicy.NONUNIFORM:
            if last_input == 0:
                return 0
            delta_percent = abs(current_input - last_input) / max(1e-9, abs(last_input)) * 100.0
            for index, edge in enumerate(self.cfg.custom_edges):
                if delta_percent < edge:
                    return index
            return len(self.cfg.custom_edges)
        else:
            # ADAPTIVE or unknown: collapse everything to slot 0
            return 0

    def select_or_create_slot(self, neuron, input_value, tick_count=0):
        """FIRST-anchor binning with capacity clamp.
        Marks `neuron.last_slot_used_fallback` whenever a new bin is desired but capacity forces reuse.
        Never allocates a brand-new slot if capacity is already reached.
        """
        cfg = self.cfg
        # FIRST-anchor: set anchor once
        if not getattr(neuron, "focus_set", False) and getattr(cfg, "anchor_mode", "FIRST") == "FIRST":
            neuron.focus_anchor = float(input_value)
            neuron.focus_set = True

        anchor = float(getattr(neuron, "focus_anchor", 0.0))
        eps = max(1e-12, float(getattr(cfg, "epsilon_scale", 1e-6)))
        denom = max(abs(anchor), eps)
        delta_pct = abs(float(input_value) - anchor) / denom * 100.0
        bin_w = max(0.1, float(getattr(cfg, "bin_width_pct", 10.0)))
        sid_desired = int(delta_pct // bin_w)

        # Effective limit: per-neuron override wins over cfg
        neuron_limit = int(getattr(neuron, "slot_limit", -1))
        limit = neuron_limit if neuron_limit >= 0 else int(getattr(cfg, "slot_limit", 16))
        slots = neuron.slots
        at_capacity = (limit > 0 and len(slots) >= limit)

        want_new = (sid_desired not in slots)
        out_of_domain = (limit > 0 and sid_desired >= limit)
        use_fallback = out_of_domain or (at_capacity and want_new)

        # Choose actual sid
        if use_fallback and limit > 0:
            sid = (limit - 1)
            if sid not in slots:
                # Reuse any existing slot (no allocation at capacity). If none exist, create the first.
                if slots:
                    sid = next(iter(slots.keys()))
        else:
            sid = sid_desired

        # Ensure existence (respect capacity)
        if sid not in slots:
            if at_capacity:
                if not slots:
                    slots[sid] = Weight()
            else:
                slots[sid] = Weight()

        try:
            neuron.last_slot_used_fallback = bool(use_fallback)
        except Exception:
            pass
        return slots[sid]

    # -------- spatial (2D) --------
    def slot_id_2d(self, anchor_rc: Tuple[int, int], current_rc: Tuple[int, int]) -> Tuple[int, int]:
        """Return (row_bin, col_bin) using |Δrow| and |Δcol| as % of denom (per-axis).

        Denominator per axis uses max(|anchor_axis|, epsilon_scale) to avoid divide-by-zero.
        Bin widths are controlled by cfg.row_bin_width_pct / cfg.col_bin_width_pct.
        """
        anchor_row, anchor_col = int(anchor_rc[0]), int(anchor_rc[1])
        current_row, current_col = int(current_rc[0]), int(current_rc[1])

        # Use a sensible spatial epsilon to avoid exploding bins at ORIGIN (0,0).
        eps = max(1.0, float(getattr(self.cfg, "epsilon_scale", 1.0)))
        denominator_row = max(abs(anchor_row), eps)
        denominator_col = max(abs(anchor_col), eps)

        delta_percent_row = abs(current_row - anchor_row) / denominator_row * 100.0
        delta_percent_col = abs(current_col - anchor_col) / denominator_col * 100.0

        bin_width_row_pct = max(0.1, float(getattr(self.cfg, "row_bin_width_pct", 100.0)))
        bin_width_col_pct = max(0.1, float(getattr(self.cfg, "col_bin_width_pct", 100.0)))

        return int(delta_percent_row // bin_width_row_pct), int(delta_percent_col // bin_width_col_pct)

    def select_or_create_slot_2d(self, neuron, row: int, col: int):
        """2D FIRST/ORIGIN anchor + capacity clamp; ensures spatial slot exists.

        Keys are (row_bin, col_bin) tuples. When capacity is saturated, reuse a
        fallback id (limit-1, limit-1) if present; otherwise reuse any existing slot.
        Never creates a new slot at capacity. Also sets neuron.last_slot_used_fallback.
        """
        cfg = self.cfg

        # pick anchors
        anchor_mode = str(getattr(cfg, "anchor_mode", "FIRST")).upper()
        if anchor_mode == "ORIGIN":
            anchor_row, anchor_col = 0, 0
        else:
            # FIRST: set if not present
            if getattr(neuron, "focus_anchor_row", None) is None or getattr(neuron, "focus_anchor_col", None) is None:
                neuron.focus_anchor_row = int(row)
                neuron.focus_anchor_col = int(col)
            anchor_row, anchor_col = int(neuron.focus_anchor_row), int(neuron.focus_anchor_col)

        row_bin, col_bin = self.slot_id_2d((anchor_row, anchor_col), (int(row), int(col)))
        limit = int(getattr(cfg, "slot_limit", 16))

        if limit > 0:
            row_bin = min(row_bin, limit - 1)
            col_bin = min(col_bin, limit - 1)

        key_desired = (row_bin, col_bin)
        slots = neuron.slots
        # Effective limit: per-neuron override wins over cfg
        neuron_limit = int(getattr(neuron, "slot_limit", -1))
        limit = neuron_limit if neuron_limit >= 0 else int(getattr(cfg, "slot_limit", 16))
        at_capacity = (limit > 0 and len(slots) >= limit)
        want_new = (key_desired not in slots)
        use_fallback = (at_capacity and want_new)

        if use_fallback and limit > 0:
            key = (limit - 1, limit - 1)
            if key not in slots:
                if slots:
                    key = next(iter(slots.keys()))
        else:
            key = key_desired

        if key not in slots:
            if at_capacity:
                if not slots:
                    slots[key] = Weight()
            else:
                slots[key] = Weight()
        try:
            neuron.last_slot_used_fallback = bool(use_fallback)
        except Exception:
            pass
        return slots[key]

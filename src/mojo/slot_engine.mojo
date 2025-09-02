# Slot selection policy: map input deltas to integer slot ids.
struct SlotEngine:
    var percent_step: Float64 = 10.0  # used for FIXED policy

    fn slot_id(self, last_input: Float64, current_input: Float64, known_slots: Int) -> Int:

        # Simple fixed-width %delta binning (>=0 maps to even, <0 to odd).
        var delta_percent: Float64 = 0.0
        if last_input != 0.0:
            var num = current_input - last_input
            delta_percent = (num if num >= 0.0 else -num) / (last_input if last_input >= 0.0 else -last_input) * 100.0
        var bin_index = Int(delta_percent / self.percent_step)

        # Encode sign
        var sign_bit = 0 if current_input >= last_input else 1
        return bin_index * 2 + sign_bit

    fn select_anchor_slot_id(
        self,
        focus_anchor: Float64,
        input_value: Float64,
        bin_width_pct: Float64,
        epsilon_scale: Float64
    ) -> Int:
        var scale: Float64 = focus_anchor
        if scale < 0.0:
            scale = -scale
        if scale < epsilon_scale:
            scale = epsilon_scale
        var delta: Float64 = input_value - focus_anchor
        if delta < 0.0:
            delta = -delta
        var delta_pct: Float64 = 100.0 * delta / scale
        var width: Float64 = if bin_width_pct > 0.1 then bin_width_pct else 0.1
        return Int(delta_pct / width)

    fn slot_id_2d(self, anchor_row: Int, anchor_col: Int, row: Int, col: Int,
                   row_bin_width_pct: Float64, col_bin_width_pct: Float64, epsilon_scale: Float64) -> (Int, Int):
        var anchor_row_val = Float64(anchor_row); var anchor_col_val = Float64(anchor_col)
        var row_val = Float64(row);        var col_val = Float64(col)
        var denom_r = if anchor_row_val >= 0.0 then anchor_row_val else -anchor_row_val
        var denom_c = if anchor_col_val >= 0.0 then anchor_col_val else -anchor_col_val
        if denom_r < epsilon_scale: denom_r = epsilon_scale
        if denom_c < epsilon_scale: denom_c = epsilon_scale
        var dpr = row_val - anchor_row_val; if dpr < 0.0: dpr = -dpr
        var dpc = col_val - anchor_col_val; if dpc < 0.0: dpc = -dpc
        var rbin = Int((100.0 * dpr / denom_r) / (if row_bin_width_pct > 0.1 then row_bin_width_pct else 0.1))
        var cbin = Int((100.0 * dpc / denom_c) / (if col_bin_width_pct > 0.1 then col_bin_width_pct else 0.1))
        return (rbin, cbin)

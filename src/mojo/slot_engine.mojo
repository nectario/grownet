# Slot selection policy: map input deltas to integer slot ids.
struct SlotEngine:
    var percent_step: Float64 = 10.0  # used for FIXED policy

    fn slot_id(self, last_input: Float64, current_input: Float64, known_slots: Int) -> Int:

        # Simple fixed-width %delta binning (>=0 maps to even, <0 to odd).
        var delta_percent: Float64 = 0.0
        if last_input != 0.0:
            let num = current_input - last_input
            delta_percent = (num if num >= 0.0 else -num) / (last_input if last_input >= 0.0 else -last_input) * 100.0
        let bin_index = Int(delta_percent / self.percent_step)

        # Encode sign
        let sign_bit = 0 if current_input >= last_input else 1
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
        let delta_pct: Float64 = 100.0 * delta / scale
        let width: Float64 = if bin_width_pct > 0.1 then bin_width_pct else 0.1
        return Int(delta_pct / width)

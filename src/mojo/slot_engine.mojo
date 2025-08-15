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

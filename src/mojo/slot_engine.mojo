from slot_config import SlotConfig
from weight import Weight

# Forward-declare Neuron to avoid import cycle
struct Neuron: pass

# Slot selection policy and FIRST/ORIGIN anchor helpers.
struct SlotEngine:
    var percent_step: Float64 = 10.0  # legacy fixed policy helper

    fn slot_id(self, last_input: Float64, current_input: Float64, known_slots: Int) -> Int:
        var delta_percent: Float64 = 0.0
        if last_input != 0.0:
            var num = current_input - last_input
            var den = if last_input >= 0.0 then last_input else -last_input
            delta_percent = (num if num >= 0.0 else -num) / den * 100.0
        var bin_index = Int(delta_percent / self.percent_step)
        var sign_bit = 0 if current_input >= last_input else 1
        return bin_index * 2 + sign_bit

    fn select_anchor_slot_id(self, focus_anchor: Float64, input_value: Float64,
                             bin_width_pct: Float64, epsilon_scale: Float64) -> Int:
        var scale: Float64 = focus_anchor
        if scale < 0.0: scale = -scale
        if scale < epsilon_scale: scale = epsilon_scale
        var delta: Float64 = input_value - focus_anchor
        if delta < 0.0: delta = -delta
        var delta_pct: Float64 = 100.0 * delta / scale
        var width: Float64 = if bin_width_pct > 0.1 then bin_width_pct else 0.1
        return Int(delta_pct / width)

    fn slot_id_2d(self, anchor_row: Int, anchor_col: Int, row: Int, col: Int,
                  row_bin_width_pct: Float64, col_bin_width_pct: Float64, epsilon_scale: Float64) -> (Int, Int):
        var ar = Float64(anchor_row); var ac = Float64(anchor_col)
        var r = Float64(row); var c = Float64(col)
        var denom_r = if ar >= 0.0 then ar else -ar
        var denom_c = if ac >= 0.0 then ac else -ac
        if denom_r < epsilon_scale: denom_r = epsilon_scale
        if denom_c < epsilon_scale: denom_c = epsilon_scale
        var dpr = r - ar; if dpr < 0.0: dpr = -dpr
        var dpc = c - ac; if dpc < 0.0: dpc = -dpc
        var rbin = Int((100.0 * dpr / denom_r) / (if row_bin_width_pct > 0.1 then row_bin_width_pct else 0.1))
        var cbin = Int((100.0 * dpc / denom_c) / (if col_bin_width_pct > 0.1 then col_bin_width_pct else 0.1))
        return (rbin, cbin)

    # Python-parity: select_or_create_slot with strict capacity + fallback marking.
    fn select_or_create_slot(self, neuron: inout Neuron, input_value: Float64) -> Int:
        var cfg = neuron.slot_cfg
        if not neuron.focus_set and cfg.anchor_mode == SlotConfig.AnchorMode.FIRST:
            neuron.focus_anchor = input_value
            neuron.focus_set = True

        var anchor = neuron.focus_anchor
        var denom = if anchor >= 0.0 then anchor else -anchor
        if denom < (if cfg.epsilon_scale > 1e-12 then cfg.epsilon_scale else 1e-12):
            denom = (if cfg.epsilon_scale > 1e-12 then cfg.epsilon_scale else 1e-12)
        var delta = input_value - anchor; if delta < 0.0: delta = -delta
        var delta_pct = delta / denom * 100.0
        var bin_w = if cfg.bin_width_pct > 0.1 then cfg.bin_width_pct else 0.1
        var sid_desired = Int(delta_pct // bin_w)

        var limit = (neuron.slot_limit if neuron.slot_limit >= 0 else cfg.slot_limit)
        var at_capacity = (limit > 0) and (Int(neuron.slots.size()) >= limit)
        var out_of_domain = (limit > 0) and (sid_desired >= limit)
        var want_new = not neuron.slots.contains(sid_desired)
        var use_fallback = out_of_domain or (at_capacity and want_new)

        var sid = (limit - 1) if (use_fallback and limit > 0) else sid_desired
        if use_fallback and limit > 0 and not neuron.slots.contains(sid) and Int(neuron.slots.size()) > 0:
            # Reuse any existing slot id deterministically by scanning
            var i = 0
            while i < limit:
                if neuron.slots.contains(i):
                    sid = i
                    break
                i = i + 1
        if not neuron.slots.contains(sid):
            if at_capacity:
                if neuron.slots.size() == 0:
                    neuron.slots[sid] = Weight()
            else:
                neuron.slots[sid] = Weight()

        neuron.last_slot_used_fallback = use_fallback
        neuron.last_slot_id = sid
        return sid

    # Python-parity: spatial 2D variant with strict capacity + fallback.
    fn select_or_create_slot_2d(self, neuron: inout Neuron, row: Int, col: Int) -> Int:
        var cfg = neuron.slot_cfg
        if (neuron.anchor_row < 0 or neuron.anchor_col < 0):
            if cfg.anchor_mode == SlotConfig.AnchorMode.ORIGIN:
                neuron.anchor_row = 0; neuron.anchor_col = 0
            else:
                neuron.anchor_row = row; neuron.anchor_col = col

        var pair = self.slot_id_2d(neuron.anchor_row, neuron.anchor_col, row, col,
                                   cfg.row_bin_width_pct, cfg.col_bin_width_pct,
                                   (if cfg.epsilon_scale > 1.0 then cfg.epsilon_scale else 1.0))
        var rbin = pair[0]; var cbin = pair[1]
        var limit = (neuron.slot_limit if neuron.slot_limit >= 0 else cfg.slot_limit)
        var at_capacity = (limit > 0) and (Int(neuron.slots.size()) >= limit)
        var out_of_domain = (limit > 0) and ((rbin >= limit) or (cbin >= limit))
        var desired_key = rbin * 100000 + cbin
        var want_new = not neuron.slots.contains(desired_key)
        var use_fallback = out_of_domain or (at_capacity and want_new)
        var key = ((limit - 1) * 100000 + (limit - 1)) if (use_fallback and limit > 0) else desired_key

        if use_fallback and limit > 0 and not neuron.slots.contains(key) and Int(neuron.slots.size()) > 0:
            # Reuse any existing spatial key by scanning a small grid of candidates
            var i = 0
            while i < limit:
                var candidate = i * 100000 + i
                if neuron.slots.contains(candidate):
                    key = candidate
                    break
                i = i + 1
        if not neuron.slots.contains(key):
            if at_capacity:
                if neuron.slots.size() == 0:
                    neuron.slots[key] = Weight()
            else:
                neuron.slots[key] = Weight()
        neuron.last_slot_used_fallback = use_fallback
        neuron.last_slot_id = key
        return key

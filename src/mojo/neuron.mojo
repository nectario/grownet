# neuron.mojo
# Neuron with elastic slots (binned by percent change). No ownership keywords; simple Python-like Mojo.

from math_utils import percent_delta, round_one_decimal
from weight import Weight

alias SLOT_LIMIT: Int64 = -1   # -1 => unlimited

struct Neuron:
    var neuron_id: String
    var kind: String = "E"      # "E" (excitatory), "I" (inhibitory), "M" (modulatory)

    # slot memory
    var last_raw: Float64 = 0.0
    var slots: Dict[Int64, Weight] = Dict()

    # last-tick meta for Regions/Tracts
    var fired_last: Bool = False
    var last_input_value: Float64 = 0.0

    fn select_slot(self, value: Float64) -> (Int64, Weight):
        var delta = percent_delta(self.last_raw, value)
        var bin_float = round_one_decimal(delta * 10.0)   # 0.0, 0.1, 0.2, ...
        var bin_id = Int64(bin_float)                      # 0, 1, 2, ...
        if self.slots.contains(bin_id):
            # existing slot
            return (bin_id, self.slots[bin_id])
        # create new slot if allowed
        if SLOT_LIMIT == -1 or self.slots.len < SLOT_LIMIT:
            var w = Weight()
            self.slots[bin_id] = w
            return (bin_id, w)
        # fallback: reuse any existing slot (first one)
        return (self.slots.keys()[0], self.slots.values()[0])

    fn on_input(self, value: Float64, modulation_factor: Float64, inhibition_factor: Float64) -> Bool:
        var pair = self.select_slot(value)
        var w = pair[1]

        w.reinforce(modulation_factor, inhibition_factor)
        var fired = w.update_threshold(value)

        self.fired_last = fired
        self.last_input_value = value
        self.last_raw = value
        return fired

    fn neuron_value(self, mode: String) -> Float64:
        # Provide single-number summaries for logging.
        if self.slots.len == 0:
            return 0.0

        if mode == "readiness":
            var best = -1e9
            for w in self.slots.values():
                var margin = w.strength_value - w.threshold_value
                if margin > best:
                    best = margin
            return best

        if mode == "firing_rate":
            var total = 0.0
            for w in self.slots.values():
                total = total + w.ema_rate
            return total / Float64(self.slots.len)

        if mode == "memory":
            var s = 0.0
            for w in self.slots.values():
                var v = w.strength_value
                if v < 0.0:
                    v = -v
                s = s + v
            return s

        # default
        return 0.0

# unified hook
fn onOutput(self, amplitude: Float64):
    return


fn compute_percent_delta(previous: Float64, current: Float64) -> Float64:
    if previous == 0.0:
        return 1.0
    let denom = (previous < 0.0) ? -previous : previous
    let d = current - previous
    let ad = (d < 0.0) ? -d : d
    return ad / (denom if denom > 1e-9 else 1e-9)

fn select_or_create_slot(self, value: Float64) -> Int64:
    # Access policy via owning layer if available; otherwise use defaults
    var policy = SlotPolicyConfig()
    if hasattr(self, "layer") and hasattr(self.layer, "slot_policy"):
        policy = self.layer.slot_policy

    let percent = compute_percent_delta(self.last_input_value, value)
    var width = policy.slot_width_percent

    # Adaptive cooldown using region/layer tick if available; fall back to simple logic
    var tick: Int64 = self.policy_tick
    if hasattr(self, "bus"):
        tick = self.bus.current_step

    if policy.mode == "adaptive":
        if tick - self.policy_last_adjust >= policy.adjust_cooldown_ticks:
            var active: Int64 = 0
            for kv in self.slots.items():
                if kv.value.hit_count > 0: active = active + 1
            if active > policy.target_active_high:
                width = width * policy.adjust_factor_up
                if width > policy.max_slot_width: width = policy.max_slot_width
                self.policy_last_adjust = tick
            elif active < policy.target_active_low and percent > width:
                width = width * policy.adjust_factor_down
                if width < policy.min_slot_width: width = policy.min_slot_width
                self.policy_last_adjust = tick
            policy.slot_width_percent = width

    var widths = [width]
    if policy.mode == "multi_resolution":
        widths = policy.multires_widths

    # Try existing buckets
    for w in widths:
        let bucket = Int64(percent / (w if w > 1e-9 else 1e-9))
        if self.slots.contains(bucket): return bucket

    # fallback finer widths
    if len(widths) > 1:
        for i in range(1, len(widths)):
            let w = widths[i]
            let bucket = Int64(percent / (w if w > 1e-9 else 1e-9))
            if self.slots.contains(bucket): return bucket

    # Creation: pick width from nonuniform schedule if present
    var use_w = widths[len(widths)-1]
    if len(policy.nonuniform_schedule) > 0:
        let idx = len(self.slots)
        if idx < len(policy.nonuniform_schedule):
            use_w = policy.nonuniform_schedule[Int(idx)]
    let new_id = Int64(percent / (use_w if use_w > 1e-9 else 1e-9))
    if self.slot_limit >= 0 and len(self.slots) >= self.slot_limit:
        # reuse first slot
        for kv in self.slots.items(): return kv.key
    self.slots[new_id] = Weight()
    return new_id

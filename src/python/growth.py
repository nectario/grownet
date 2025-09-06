from typing import Optional, Any


class GrowthPolicy:
    """Policy knobs for automatic region layer growth.

    - enable_layer_growth: master toggle
    - max_total_layers: hard cap (-1 = unlimited)
    - avg_slots_threshold: trigger on avg(slots per neuron) >= value
    - percent_neurons_at_cap_threshold: OR-trigger on % neurons at cap using fallback
    - layer_cooldown_ticks: min ticks between layer growth events
    - new_layer_excitatory_count: size of the new (excit-only) layer
    - wire_probability: probability to wire previous → new (default 1.0)
    """

    def __init__(
        self,
        enable_layer_growth: bool = True,
        max_total_layers: int = -1,
        avg_slots_threshold: float = 8.0,
        percent_neurons_at_cap_threshold: float = 50.0,
        layer_cooldown_ticks: int = 25,
        new_layer_excitatory_count: int = 4,
        wire_probability: float = 1.0,
    ) -> None:
        self.enable_layer_growth = bool(enable_layer_growth)
        self.max_total_layers = int(max_total_layers)
        self.avg_slots_threshold = float(avg_slots_threshold)
        self.percent_neurons_at_cap_threshold = float(percent_neurons_at_cap_threshold)
        self.layer_cooldown_ticks = int(layer_cooldown_ticks)
        self.new_layer_excitatory_count = int(new_layer_excitatory_count)
        self.wire_probability = float(wire_probability)


def is_trainable_layer(layer_obj: Any) -> bool:
    name = layer_obj.__class__.__name__.lower()
    return ("input" not in name) and ("output" not in name) and hasattr(layer_obj, "get_neurons")


def maybe_grow(region, policy: Optional[GrowthPolicy]) -> bool:
    """Inspect region after end-of-tick and add a spillover layer if pressure is high.

    Returns True if a new layer was added.
    """
    if policy is None or not getattr(policy, "enable_layer_growth", True):
        return False

    # Cap total layers
    try:
        total_layers = len(region.get_layers())
        if policy.max_total_layers > 0 and total_layers >= policy.max_total_layers:
            return False
    except Exception:
        return False

    # Cooldown window from any layer bus step (advanced in end_tick)
    now = 0
    try:
        layers = region.get_layers()
        if layers:
            now = int(layers[0].get_bus().get_current_step())
    except Exception:
        now = 0

    last_step = int(getattr(region, "last_layer_growth_step", -1))
    if last_step >= 0 and (now - last_step) < int(policy.layer_cooldown_ticks):
        return False

    # Collect candidate layers and neurons
    try:
        all_layers = region.get_layers()
    except Exception:
        return False

    trainable_indices = [i for i, layer in enumerate(all_layers) if is_trainable_layer(layer)]
    if not trainable_indices:
        return False

    neuron_list = []
    for index in trainable_indices:
        try:
            neuron_list.extend(all_layers[index].get_neurons())
        except Exception:
            pass

    if not neuron_list:
        return False

    # Region pressure
    neuron_count = len(neuron_list)
    total_slots = 0
    saturated_with_fallback = 0
    for neuron in neuron_list:
        try:
            slots_map = getattr(neuron, "slots", {})
            total_slots += len(slots_map)
            slot_limit = int(getattr(neuron, "slot_limit", -1))
            at_capacity = (slot_limit >= 0 and len(slots_map) >= slot_limit)
            used_fallback = bool(getattr(neuron, "last_slot_used_fallback", False))
            if at_capacity and used_fallback:
                saturated_with_fallback += 1
        except Exception:
            pass

    avg_slots_per_neuron = (float(total_slots) / float(neuron_count)) if neuron_count > 0 else 0.0
    pct_saturated = (100.0 * float(saturated_with_fallback) / float(neuron_count)) if neuron_count > 0 else 0.0

    if not (
        avg_slots_per_neuron >= float(policy.avg_slots_threshold)
        or pct_saturated >= float(policy.percent_neurons_at_cap_threshold)
    ):
        return False

    # Pick the most saturated trainable layer as source
    best_layer_index = -1
    best_score = -1.0
    for index in trainable_indices:
        layer_obj = all_layers[index]
        try:
            layer_neurons = layer_obj.get_neurons()
            if not layer_neurons:
                continue
            saturated = 0
            for neuron in layer_neurons:
                slots_map = getattr(neuron, "slots", {})
                slot_limit = int(getattr(neuron, "slot_limit", -1))
                at_capacity = (slot_limit >= 0 and len(slots_map) >= slot_limit)
                used_fallback = bool(getattr(neuron, "last_slot_used_fallback", False))
                if at_capacity and used_fallback:
                    saturated += 1
            score = float(saturated) / float(len(layer_neurons))
            if score > best_score:
                best_score = score
                best_layer_index = index
        except Exception:
            continue

    if best_layer_index < 0:
        best_layer_index = trainable_indices[-1]

    # Add spillover layer and wire prev → new
    try:
        new_e = max(1, int(policy.new_layer_excitatory_count))
        new_index = region.add_layer(excitatory_count=new_e, inhibitory_count=0, modulatory_count=0)
        region.connect_layers(best_layer_index, new_index, probability=float(policy.wire_probability), feedback=False)
        setattr(region, "last_layer_growth_step", now)
        return True
    except Exception:
        return False

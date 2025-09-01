class Tract:
    """Bridges two layers by subscribing to source fires and routing to dest.

    Extended to optionally pass 2D context and/or deterministic sinks.
    """
    def __init__(self, src_layer, dst_layer, region_bus=None, feedback=False,
                 probability: float | None = None,
                 allowed_source_indices: set[int] | None = None,
                 sink_map: dict[int, list[int]] | None = None):
        self.src = src_layer
        self.dst = dst_layer
        self.region_bus = region_bus
        self.feedback = bool(feedback)
        self._sink_map = sink_map or {}
        self._allowed = allowed_source_indices  # if None: allow all

        # capture source shape if 2D
        self.src_height = getattr(self.src, "height", None)
        self.src_width = getattr(self.src, "width", None)

        # subscribe to source neuron fires
        for src_index, neuron in enumerate(self.src.get_neurons()):
            if self._allowed is not None and src_index not in self._allowed:
                continue
            def make_hook(i):
                return lambda who, value: self.on_source_fired(i, value)
            neuron.register_fire_hook(make_hook(src_index))

    def on_source_fired(self, source_index, value):
        # If we have an explicit sink map (e.g., windowed wiring to OutputLayer2D), deliver directly
        targets = self._sink_map.get(source_index)
        if targets:
            try:
                neurons = self.dst.get_neurons()
                for t_idx in targets:
                    if 0 <= t_idx < len(neurons):
                        n = neurons[t_idx]
                        fired = n.on_input(value)
                        if fired:
                            n.on_output(value)
                return
            except Exception:
                pass

        # Otherwise, prefer 2D-aware propagation if shape is known and dst supports it
        if self.src_height is not None and self.src_width is not None and hasattr(self.dst, "propagate_from_2d"):
            self.dst.propagate_from_2d(source_index, value, int(self.src_height), int(self.src_width))
            return

        # Fallback: let the destination layer handle generic propagate
        self.dst.propagate_from(source_index, value)

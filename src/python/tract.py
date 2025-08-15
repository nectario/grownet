class Tract:
    def __init__(self, src_layer, dst_layer, region_bus=None, feedback=False):
        self._src = src_layer
        self._dst = dst_layer
        self._region_bus = region_bus
        self._feedback = bool(feedback)
        # subscribe to each source neuron fire via the layer's wiring scheme:
        for idx, n in enumerate(self._src.get_neurons()):
            # capture idx for closure
            def make_hook(i):
                return lambda who, value: self.on_source_fired(i, value)
            n.register_fire_hook(make_hook(idx))

    def on_source_fired(self, source_index, value):
        # forward to destination layer; let the layer decide how to handle
        self._dst.propagate_from(source_index, value)

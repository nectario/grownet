class Tract:
    def __init__(self, src_layer, dst_layer, region_bus=None, feedback=False):
        self.src = src_layer
        self.dst = dst_layer
        self.region_bus = region_bus
        self.feedback = bool(feedback)
        # subscribe to each source neuron fire via the layer's wiring scheme:
        for src_index, neuron in enumerate(self.src.get_neurons()):
            # capture idx for closure
            def make_hook(i):
                return lambda who, value: self.on_source_fired(i, value)
            neuron.register_fire_hook(make_hook(src_index))

    def on_source_fired(self, source_index, value):
        # forward to destination layer; let the layer decide how to handle
        self.dst.propagate_from(source_index, value)

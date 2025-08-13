from weight import Weight, absf

alias DEFAULT_SMOOTHING: Float64 = 0.20

struct LateralBus:
    var inhibition_factor: Float64
    var modulation_factor: Float64

    fn __init__() -> Self:
        return Self(1.0, 1.0)

    fn decay(mut self ):
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0

struct NeuronType:
    alias EXCITATORY: Int64 = 0
    alias INHIBITORY: Int64 = 1
    alias MODULATORY: Int64 = 2
    alias INPUT:      Int64 = 3
    alias OUTPUT:     Int64 = 4

fn percent_delta(last_value: Float64, value: Float64) -> Float64:
    if last_value == 0.0:
        return 0.0
    let denom = absf(last_value)
    return 100.0 * absf(value - last_value) / denom

struct Neuron:
    var neuron_type: Int64
    var slots: Dict[Int64, Weight]
    var fired_last: Bool
    var last_input_value: Float64
    var bus: LateralBus

    # Output-only accumulators
    var accumulated_sum: Float64
    var accumulated_count: Int64
    var output_value: Float64
    var smoothing: Float64

    fn __init__(neuron_type: Int64, bus: LateralBus, smoothing: Float64 = DEFAULT_SMOOTHING) -> Self:
        return Self(
            neuron_type = neuron_type,
            slots = Dict[Int64, Weight](),
            fired_last = False,
            last_input_value = 0.0,
            bus = bus,
            accumulated_sum = 0.0,
            accumulated_count = 0,
            output_value = 0.0,
            smoothing = smoothing
        )

    fn slot_id_for(self, value: Float64, slot_width_percent: Float64 = 10.0) -> Int64:
        if self.neuron_type == NeuronType.INPUT or self.neuron_type == NeuronType.OUTPUT:
            return 0
        let pct = percent_delta(self.last_input_value, value)
        let width = (slot_width_percent if slot_width_percent > 1e-9 else 1e-9)
        return Int64(pct / width)

    fn on_input(mut self , value: Float64) -> Bool:
        var id = self.slot_id_for(value, 10.0)
        var slot = self.slots.get(id)
        if slot is None:
            slot = Weight()
        slot.reinforce(self.bus.modulation_factor, self.bus.inhibition_factor)
        let fired = slot.update_threshold(value)

        # write-back (Dict elements are values)
        self.slots[id] = slot
        self.fired_last = fired
        self.last_input_value = value
        return fired

    fn on_output(mut self , amplitude: Float64):
        # Unified hook:
        if self.neuron_type == NeuronType.OUTPUT:
            self.accumulated_sum += amplitude
            self.accumulated_count += 1
        elif self.neuron_type == NeuronType.INHIBITORY:
            # one-tick mild inhibition; Region/Layer will decay the bus
            self.bus.inhibition_factor = 0.80
        elif self.neuron_type == NeuronType.MODULATORY:
            self.bus.modulation_factor = 1.20
        # Excitatory/Input: no-op here

    fn end_tick(mut self ):
        if self.neuron_type != NeuronType.OUTPUT:
            return
        if self.accumulated_count > 0:
            let mean = self.accumulated_sum / Float64(self.accumulated_count)
            self.output_value = (1.0 - self.smoothing) * self.output_value + self.smoothing * mean
        self.accumulated_sum = 0.0
        self.accumulated_count = 0

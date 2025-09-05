from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron
from neuron import Neuron
from lateral_bus import LateralBus
from slot_engine import SlotEngine

struct Spike:
    var neuron_index: Int
    var amplitude: Float64

struct Layer:
    var neurons_exc: list[ExcitatoryNeuron]
    var neurons_inh: list[InhibitoryNeuron]
    var neurons_mod: list[ModulatoryNeuron]
    var bus: LateralBus
    var region: any

    fn init(mut self, excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> None:
        self.neurons_exc = []
        self.neurons_inh = []
        self.neurons_mod = []
        self.bus = LateralBus()
        var neuron_index = 0
        while neuron_index < excitatory_count:
            self.neurons_exc.append(ExcitatoryNeuron("E" + String(neuron_index)))
            neuron_index += 1
        neuron_index = 0
        while neuron_index < inhibitory_count:
            self.neurons_inh.append(InhibitoryNeuron("I" + String(neuron_index)))
            neuron_index += 1
        neuron_index = 0
        while neuron_index < modulatory_count:
            self.neurons_mod.append(ModulatoryNeuron("M" + String(neuron_index)))
            neuron_index += 1

        # Share the same bus across all neuron cores (Python parity)
        for e in self.neurons_exc: e.core.bus = self.bus
        for i in self.neurons_inh: i.core.bus = self.bus
        for m in self.neurons_mod: m.core.bus = self.bus

    fn get_neurons(self) -> list[Neuron]:
        var alln = []
        for n in self.neurons_inh: alln.append(n.core)
        for n in self.neurons_mod: alln.append(n.core)
        for n in self.neurons_exc: alln.append(n.core)
        return alln

    fn forward(mut self, value: Float64) -> None:
        # Inhibit/modulate classes can express pulses in on_output; execute in order
        for n in self.neurons_inh:
            if n.on_input(value): n.on_output(value)
        for n in self.neurons_mod:
            if n.on_input(value): n.on_output(value)
        for n in self.neurons_exc:
            if n.on_input(value): n.on_output(value)

    fn propagate_from(mut self, source_index: Int, value: Float64) -> None:
        # Default: treat like uniform drive from external source
        self.forward(value)

    fn propagate_from_2d(mut self, source_index: Int, value: Float64, height: Int, width: Int) -> None:
        # Compute (row,col) from flattened index and call spatial on_input if available
        var row = source_index / width
        var col = source_index % width
        for n in self.get_neurons():
            if n.on_input_2d(value, row, col): n.on_output(value)

    fn end_tick(mut self) -> None:
        # Growth escalation (fallback streak + cooldown)
        var now = self.bus.get_current_step()
        var alln = self.get_neurons()
        var i = 0
        while i < alln.len:
            var n = alln[i]
            var slot_config = n.slot_cfg
            if slot_config.growth_enabled and slot_config.neuron_growth_enabled:
                var at_capacity: Bool = (n.slot_limit >= 0) and (Int(n.slots.size()) >= n.slot_limit)
                if at_capacity and n.last_slot_used_fallback:
                    if n.fallback_streak >= (if slot_config.fallback_growth_threshold > 0 then slot_config.fallback_growth_threshold else 1):
                        var cooldown = if slot_config.neuron_growth_cooldown_ticks > 0 then slot_config.neuron_growth_cooldown_ticks else 0
                        if (n.last_growth_tick < 0) or (now - n.last_growth_tick >= cooldown):
                            # Grow same kind via helper (includes autowiring)
                            var new_unified_index = self.try_grow_neuron(n)
                            n.last_growth_tick = now
                            n.fallback_streak = 0
            i = i + 1
        # Bus decay increments current_step
        self.bus.decay()

    fn get_bus(self) -> LateralBus:
        return self.bus

    fn set_region(mut self, region_ref: any) -> None:
        self.region = region_ref

    # Same-kind neuron growth helper (E/I/M), returns unified neuron index and autowires it
    fn try_grow_neuron(mut self, seed: Neuron) -> Int:
        var slot_config = seed.slot_cfg
        # Determine seed kind by membership
        var group_index = 0
        while group_index < self.neurons_inh.len:
            if self.neurons_inh[group_index].core == seed:
                var new_inhibitory = InhibitoryNeuron("G" + String(self.get_neurons().len))
                new_inhibitory.core.bus = self.bus
                new_inhibitory.core.slot_cfg = slot_config
                new_inhibitory.core.slot_engine = SlotEngine(slot_config)
                new_inhibitory.core.slot_limit = seed.slot_limit
                self.neurons_inh.append(new_inhibitory)
                var new_unified_index = (self.neurons_inh.len - 1)  # unified = inhibitory index
                if (self.region is not None) and (self.region.autowire_new_neuron_by_ref is not None):
                    self.region.autowire_new_neuron_by_ref(self, new_unified_index)
                return new_unified_index
            group_index = group_index + 1

        group_index = 0
        while group_index < self.neurons_mod.len:
            if self.neurons_mod[group_index].core == seed:
                var new_modulatory = ModulatoryNeuron("G" + String(self.get_neurons().len))
                new_modulatory.core.bus = self.bus
                new_modulatory.core.slot_cfg = slot_config
                new_modulatory.core.slot_engine = SlotEngine(slot_config)
                new_modulatory.core.slot_limit = seed.slot_limit
                self.neurons_mod.append(new_modulatory)
                var new_unified_index_mod = self.neurons_inh.len + (self.neurons_mod.len - 1)
                if (self.region is not None) and (self.region.autowire_new_neuron_by_ref is not None):
                    self.region.autowire_new_neuron_by_ref(self, new_unified_index_mod)
                return new_unified_index_mod
            group_index = group_index + 1

        # Default to excitatory
        var new_excitatory = ExcitatoryNeuron("G" + String(self.get_neurons().len))
        new_excitatory.core.bus = self.bus
        new_excitatory.core.slot_cfg = slot_config
        new_excitatory.core.slot_engine = SlotEngine(slot_config)
        new_excitatory.core.slot_limit = seed.slot_limit
        self.neurons_exc.append(new_excitatory)
        var new_unified_index_exc = self.neurons_inh.len + self.neurons_mod.len + (self.neurons_exc.len - 1)
        if (self.region is not None) and (self.region.autowire_new_neuron_by_ref is not None):
            self.region.autowire_new_neuron_by_ref(self, new_unified_index_exc)
        return new_unified_index_exc

class LateralBus:
    """
    Shared per-layer bus for simple, time-local signals.
      - inhibition_factor: 0..1 scales down strength after reinforcement
      - modulation_factor: scales learning rate (step_value)
      - current_step: monotonic tick so synapses can record 'last used'
    """
    def __init__(self):
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
        self.current_step = 0

    def decay(self):
        # Reset to neutral each tick (later: add decay constants if needed)
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
        self.current_step += 1

# PYTHON patches you should apply if not present already

1) neuron.py — add a default onOutput
   --------------------------------------------------
   class Neuron:
       ...
       def onOutput(self, amplitude: float) -> None:
           return

2) layer.py — when a neuron fires, call onOutput before propagation
   --------------------------------------------------
   fired = neuron.onInput(x)
   if fired:
       neuron.onOutput(x)            # NEW: unified hook
       self.propagate_from(i, x)     # or whatever your layer does on fire

3) OutputLayer2D.propagate_from — already included here:
   --------------------------------------------------
   fired = n.onInput(value)
   if fired:
       n.onOutput(value)

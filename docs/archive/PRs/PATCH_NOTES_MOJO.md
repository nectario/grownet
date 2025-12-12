# Mojo patches for unified onInput / onOutput

Apply these small changes to your existing Mojo core files:

1) **neuron.mojo**
   - Rename the method:
     ```mojo
     fn on_input(self, value: Float64, modulation_factor: Float64, inhibition_factor: Float64) -> Bool
     ```
     to
     ```mojo
     fn onInput(self, value: Float64, modulationFactor: Float64, inhibitionFactor: Float64) -> Bool
     ```
     (Just rename the function and parameter names; internal logic unchanged.)
   - Add a default no-op hook:
     ```mojo
     fn onOutput(self, amplitude: Float64):
         pass
     ```

2) **layer.mojo**
   Wherever you currently do something like:
   ```mojo
   let fired = neuron.on_input(x, bus.modulation_factor, bus.inhibition_level)
   if fired:
       # existing propagation
       self.propagate_from(i, x)
   ```
   update it to:
   ```mojo
   let fired = neuron.onInput(x, bus.modulation_factor, bus.inhibition_level)
   if fired:
       neuron.onOutput(x)           # NEW unified hook
       self.propagate_from(i, x)    # as before
   ```

3) **OutputLayer2D** and **InputLayer2D**
   The versions included in this pack already use `onInput`/`onOutput`. If you keep your own,
   ensure that after computing `fired`, you call `neuron.onOutput(value)` for consistency.

Notes:
- Keep using `alias` for constants.
- We keep your existing field names (e.g., `threshold_value`, `first_seen`) from `weight.mojo`.
- No underscores in *function* names; variables can stay as-is to match your current files.

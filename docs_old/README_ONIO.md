# GrowNet — Unified onInput / onOutput (Python & Java)

This pack updates Input/Output neuron & 2D-layer code so *every neuron*
follows the same two-method contract:
  - `onInput(value, ...) -> bool`: returns whether the neuron fired
  - `onOutput(amplitude) -> None`: called **only if** the neuron fired

## What to update in your project
- **Base Neuron**: add a default `onOutput(self, amplitude)` / `onOutput(double amplitude)` that does nothing.
- **Layer** (hidden/standard): wherever you already check a neuron firing, add:
    `if (fired) { neuron.onOutput(value); ... }`
  *Do this in both Python and Java.*
- **Input/Output 2D layers** in this pack already call `onInput` and (if fired) `onOutput` consistently.
- **OutputNeuron**: never calls `fire(...)`; it is an actuator/sink.
  **InputNeuron**: keeps the `fire(...)` call on successful `onInput` so events route as before.

If you see duplicate routing, remove the `self.fire(...)` call in `InputNeuron.onInput` and let your Layer drive propagation.

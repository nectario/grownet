# C++ patches for unified onInput / onOutput

1) **Neuron.h**
   Add a default no-op:
   ```cpp
   virtual void onOutput(double amplitude) {}
   ```

2) **Layer.h**
   Wherever you handle a neuron's input and check `fired`, insert:
   ```cpp
   bool fired = neuron->onInput(x, getBus());
   if (fired) {
       neuron->onOutput(x);         // NEW unified hook
       propagateFrom(i, x);         // existing behavior
   }
   ```

3) **OutputLayer2D.h**
   Use:
   ```cpp
   bool fired = n->onInput(value, getBus());
   if (fired) n->onOutput(value);
   ```

4) **InputLayer2D.h**
   When driving pixels:
   ```cpp
   bool fired = n->onInput(image[y][x], getBus());
   if (fired) n->onOutput(image[y][x]); // no-op hook
   ```

Notes:
- The unified contract makes output neurons proper "sinks": they do not propagate on `onInput`.
- Hidden and input neurons can still call `fire(...)` inside `onInput` if that matches your current routing design.

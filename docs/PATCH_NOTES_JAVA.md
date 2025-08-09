# JAVA patches you should apply if not present already

1) Neuron.java — add a default onOutput
   --------------------------------------------------
   public class Neuron {
       ...
       public void onOutput(double amplitude) { /* no-op by default */ }
   }

2) Layer.java — when a neuron fires, call onOutput before propagation
   --------------------------------------------------
   boolean fired = neuron.onInput(x, bus.getModulationFactor(), bus.getInhibitionFactor());
   if (fired) {
       neuron.onOutput(x);            // NEW: unified hook
       propagateFrom(i, x);           // existing behavior
   }

3) OutputLayer2D.propagateFrom — already included here:
   --------------------------------------------------
   boolean fired = n.onInput(value, getBus().getModulationFactor(), getBus().getInhibitionFactor());
   if (fired) n.onOutput(value);

package ai.nektron.grownet;

@FunctionalInterface
public interface FireHook {
    /** Called when a neuron fires (after its intra‑layer propagation completes). */
    void onFire(double inputValue, Neuron self);
}

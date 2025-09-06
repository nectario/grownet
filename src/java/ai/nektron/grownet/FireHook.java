package ai.nektron.grownet;

/** Callback invoked after a neuron fires. */
@FunctionalInterface
public interface FireHook {
    void onFire(double inputValue, Neuron neuron);
}
package ai.nektron.grownet;

/** Standard excitatory neuron uses base fire() behaviour. */
public class ExcitatoryNeuron extends Neuron {
    public ExcitatoryNeuron(String id, LateralBus bus) {
        super(id, bus);
    }
    // inherits default fire()
}
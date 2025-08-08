package ai.nektron.grownet;

/** Directed edge: source neuron --(weight)--> target neuron, with routing metadata. */
public final class Synapse {
    public final Weight weight = new Weight();
    public final Neuron target;
    public final boolean feedback;
    public long lastStep = 0L;

    public Synapse(Neuron target, boolean feedback) {
        this.target = target;
        this.feedback = feedback;
    }

    public Weight getWeight() {
        return weight;
    }

    public Neuron getTarget() {
        return target;
    }
}

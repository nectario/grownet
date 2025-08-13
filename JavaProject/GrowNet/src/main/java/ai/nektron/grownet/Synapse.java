package ai.nektron.grownet;

/**
 * Directed connection from a source neuron to a target neuron.
 * Holds its own Weight and last-step timestamp.
 */
public class Synapse {
    private final Neuron target;
    private final boolean feedback;
    private final Weight weight = new Weight();
    long lastStep = 0L;

    public Synapse(Neuron target, boolean feedback) {
        this.target = target;
        this.feedback = feedback;
    }

    public Neuron getTarget()    { return target; }
    public boolean isFeedback()  { return feedback; }
    public Weight getWeight()    { return weight;  }
}
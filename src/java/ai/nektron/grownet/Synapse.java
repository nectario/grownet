package ai.nektron.grownet;

public final class Synapse {
    private final Neuron target;
    private final Weight weight;
    private final boolean feedback;
    private long lastStep;

    public Synapse(Neuron target, boolean feedback) {
        this.target = target;
        this.feedback = feedback;
        this.weight  = new Weight();     // fresh edge-compartment
        this.lastStep = 0L;
    }

    public Neuron getTarget() { return target; }
    public Weight getWeight() { return weight; }
    public boolean isFeedback() { return feedback; }

    public long getLastStep() { return lastStep; }
    public void setLastStep(long step) { this.lastStep = step; }
}

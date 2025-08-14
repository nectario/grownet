package ai.nektron.grownet;

final class Synapse {
    final Neuron target;
    final boolean feedback;
    final Weight weight = new Weight();
    long lastStep = 0;

    Synapse(Neuron target, boolean feedback) {
        this.target = target;
        this.feedback = feedback;
    }
}

package ai.nektron.grownet;

public class InputNeuron extends Neuron {
    private final double gain;
    private final double epsilonFire;

    public InputNeuron(String name, double gain, double epsilonFire) {
        super(name);
        this.gain = gain;
        this.epsilonFire = epsilonFire;
        getSlots().computeIfAbsent(0, k -> new Weight());
    }

    private static double clamp01(double x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }

    /** Unified onInput: single-slot gate; still calls fire(...) so routing works as before. */
    public boolean onInput(double value, double modulation, double inhibition) {
        double stimulus  = clamp01(value * gain);
        double effective = clamp01(stimulus * modulation * inhibition);

        Weight slot = getSlots().get(0);
        if (!slot.isSeenFirst()) {
            slot.updateThreshold(Math.max(0.0, effective * (1.0 - epsilonFire)));
            slot.setSeenFirst(true);
        }
        slot.setStrengthValue(effective);

        boolean fired = slot.updateThreshold(effective);
        setFiredLast(fired);
        setLastInputValue(effective);
        if (fired) { fire(effective); } // keep routing semantics
        return fired;
    }

    @Override
    public void onOutput(double amplitude) {
        // input neurons do not write; hook reserved for metrics/logging
    }
}

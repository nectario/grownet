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

    public boolean onSensorValue(double value, double modulation, double inhibition) {
        double stimulus  = clamp01(value * gain);
        double effective = clamp01(stimulus * modulation * inhibition);

        Weight slot = getSlots().get(0);
        if (!slot.isFirstSeen()) {
            slot.setThresholdValue(Math.max(0.0, effective * (1.0 - epsilonFire)));
            slot.setFirstSeen(true);
        }
        slot.setStrengthValue(effective);

        boolean fired = slot.updateThreshold(effective);
        setFiredLast(fired);
        setLastInputValue(effective);
        if (fired) fire(effective);
        return fired;
    }
}

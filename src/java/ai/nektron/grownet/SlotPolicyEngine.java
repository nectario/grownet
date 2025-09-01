package ai.nektron.grownet;

import java.util.List;
import java.util.Map;

/** Stateless slot‑selection helpers used by Neuron. */
public final class SlotPolicyEngine {
    private SlotPolicyEngine() {}

    /** |Δ| as a percent of the (nonzero) previous value; first stimulus → 0.0. */
    public static double computePercentDelta(Double lastValue, double value) {
        if (lastValue == null || lastValue == 0.0) return 0.0;
        double denom = Math.max(1e-9, Math.abs(lastValue));
        return 100.0 * Math.abs(value - lastValue) / denom;
    }

    /**
     * Decide the percent‑bucket for this input; create the slot when needed.
     * Works for single‑width and multi‑resolution policies.
     * Returns the chosen bucket id.
     */
    public static int selectOrCreateSlot(Neuron neuron, double value, SlotPolicyConfig policy) {
        double percent = computePercentDelta(neuron.getLastInputValue(), value);

        // Choose a width schedule
        double[] widths;
        List<Double> multi = policy.getMultiresWidths();
        if (policy.getMode() == SlotPolicyConfig.Mode.MULTI_RESOLUTION
                && multi != null && !multi.isEmpty()) {
            widths = new double[multi.size()];
            for (int i = 0; i < multi.size(); i++) widths[i] = multi.get(i);
        } else {
            widths = new double[] { policy.getSlotWidthPercent() }; // default single width
        }

        Map<Integer, Weight> slots = neuron.getSlots();

        // Reuse if possible (coarse → fine)
        for (double w : widths) {
            int bucket = (int) Math.floor(percent / Math.max(1e-9, w));
            if (slots.containsKey(bucket)) return bucket;
        }

        // Otherwise create at the finest resolution
        double finest = widths[widths.length - 1];
        int bucket = (int) Math.floor(percent / Math.max(1e-9, finest));
        slots.computeIfAbsent(bucket, k -> new Weight());
        return bucket;
    }
}

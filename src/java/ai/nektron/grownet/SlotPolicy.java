package ai.nektron.grownet;

import java.util.List;

/** Policy for mapping an input delta to a slot id. */
public interface SlotPolicy {
    /** Compute a non-negative slot id given previous and current input. */
    int slotId(double lastInput, boolean hasLast, double currentInput);

    /** Uniform bins of fixed percent width (e.g., 10% -> bins 0,1,2,...) */
    static SlotPolicy uniformFixed(double percentStep) {
        double step = Math.max(1e-6, percentStep);
        return (last, hasLast, current) -> {
            if (!hasLast || last == 0.0) return 0;
            double deltaPercent = Math.abs(current - last) / Math.abs(last) * 100.0;
            if (deltaPercent == 0.0) return 0;
            return (int) Math.ceil(deltaPercent / step);
        };
    }

    /** Non-uniform bins with explicit boundaries (percent). Example: [5,10,20,40]. */
    static SlotPolicy nonUniform(List<Double> boundariesPercent) {
        final double[] b = boundariesPercent.stream().mapToDouble(v -> Math.max(0.0, v)).toArray();
        return (last, hasLast, current) -> {
            if (!hasLast || last == 0.0) return 0;
            double deltaPercent = Math.abs(current - last) / Math.abs(last) * 100.0;
            for (int i = 0; i < b.length; i++) {
                if (deltaPercent <= b[i]) return i; // bin index
            }
            return b.length; // tail bin
        };
    }

    /**
     * Simple adaptive policy: start with stepPercent; if we observe too many hits in the top bin,
     * create a finer-grained bin by halving the step size up to a minimum.
     */
    static SlotPolicy adaptive(double initialStepPercent, double minStepPercent, int expandEveryHits) {
        return new SlotPolicy() {
            double step = Math.max(minStepPercent, initialStepPercent);
            int topBinHits = 0;

            @Override
            public int slotId(double last, boolean hasLast, double current) {
                if (!hasLast || last == 0.0) return 0;
                double deltaPercent = Math.abs(current - last) / Math.abs(last) * 100.0;
                int bin = (deltaPercent == 0.0) ? 0 : (int) Math.ceil(deltaPercent / step);
                if (bin >= 4) { // treat >=4 as top tail for this simple heuristic
                    topBinHits++;
                    if (topBinHits >= expandEveryHits && step > minStepPercent + 1e-9) {
                        step = Math.max(minStepPercent, step * 0.5);
                        topBinHits = 0;
                    }
                }
                return bin;
            }
        };
    }
}
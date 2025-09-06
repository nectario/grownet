package ai.nektron.grownet;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** Slot selection & creation policy (kept simple and immutable‑ish). */
public final class SlotPolicyConfig {

    public enum Mode { FIXED, MULTI_RESOLUTION, ADAPTIVE }

    private final Mode mode;
    private final double slotWidthPercent;
    private final List<Double> multiresWidths;

    // Reserved for future adaptive policy (kept for API parity with Python)
    private final int  boundaryRefineHits;
    private final int  targetActiveLow;
    private final int  targetActiveHigh;
    private final double minSlotWidth;
    private final double maxSlotWidth;
    private final int  adjustCooldownTicks;
    private final double adjustFactorUp;
    private final double adjustFactorDown;
    private final List<Double> nonuniformSchedule;

    public SlotPolicyConfig() {
        this(
                Mode.FIXED,
                0.10,
                Arrays.asList(0.10, 0.05, 0.02),
                5, 6, 12,
                0.01, 0.20,
                200, 1.2, 0.9,
                null
        );
    }

    public SlotPolicyConfig(
            Mode mode,
            double slotWidthPercent,
            List<Double> multiresWidths,
            int boundaryRefineHits,
            int targetActiveLow,
            int targetActiveHigh,
            double minSlotWidth,
            double maxSlotWidth,
            int adjustCooldownTicks,
            double adjustFactorUp,
            double adjustFactorDown,
            List<Double> nonuniformSchedule
    ) {
        this.mode = (mode == null) ? Mode.FIXED : mode;
        this.slotWidthPercent = slotWidthPercent;
        this.multiresWidths = (multiresWidths == null)
                ? Arrays.asList(0.10, 0.05, 0.02)
                : Collections.unmodifiableList(new ArrayList<>(multiresWidths));

        this.boundaryRefineHits = boundaryRefineHits;
        this.targetActiveLow = targetActiveLow;
        this.targetActiveHigh = targetActiveHigh;
        this.minSlotWidth = minSlotWidth;
        this.maxSlotWidth = maxSlotWidth;
        this.adjustCooldownTicks = adjustCooldownTicks;
        this.adjustFactorUp = adjustFactorUp;
        this.adjustFactorDown = adjustFactorDown;
        this.nonuniformSchedule = (nonuniformSchedule == null)
                ? null
                : Collections.unmodifiableList(new ArrayList<>(nonuniformSchedule));
    }

    public static SlotPolicyConfig defaults() { return new SlotPolicyConfig(); }

    public Mode getMode() { return mode; }
    public double getSlotWidthPercent() { return slotWidthPercent; }
    public List<Double> getMultiresWidths() { return multiresWidths; }

    public int getBoundaryRefineHits() { return boundaryRefineHits; }
    public int getTargetActiveLow() { return targetActiveLow; }
    public int getTargetActiveHigh() { return targetActiveHigh; }
    public double getMinSlotWidth() { return minSlotWidth; }
    public double getMaxSlotWidth() { return maxSlotWidth; }
    public int getAdjustCooldownTicks() { return adjustCooldownTicks; }
    public double getAdjustFactorUp() { return adjustFactorUp; }
    public double getAdjustFactorDown() { return adjustFactorDown; }
    public List<Double> getNonuniformSchedule() { return nonuniformSchedule; }
}

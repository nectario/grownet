package ai.nektron.grownet;

import java.util.Arrays;
import java.util.List;

public class SlotPolicyConfig {
    public enum Mode { FIXED, MULTI_RESOLUTION, ADAPTIVE }
    public Mode mode = Mode.FIXED;
    public double slotWidthPercent = 0.10;
    public List<Double> multiresWidths = Arrays.asList(0.10, 0.05, 0.02);
    public int boundaryRefineHits = 5;
    public int targetActiveLow = 6;
    public int targetActiveHigh = 12;
    public double minSlotWidth = 0.01;
    public double maxSlotWidth = 0.20;
    public int adjustCooldownTicks = 200;
    public double adjustFactorUp = 1.2;
    public double adjustFactorDown = 0.9;
    public List<Double> nonuniformSchedule = null;
}

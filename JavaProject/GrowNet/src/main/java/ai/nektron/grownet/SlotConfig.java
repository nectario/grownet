package ai.nektron.grownet;

import java.util.ArrayList;
import java.util.List;

public final class SlotConfig {
    public enum Policy { FIXED, NONUNIFORM, ADAPTIVE }

    public Policy policy = Policy.FIXED;
    public double slotWidthPercent = 10.0;      // FIXED/ADAPTIVE seed
    public final List<Double> nonuniformEdges = new ArrayList<>(); // ascending
    public int maxSlots = -1;                   // -1 = unbounded

    public SlotConfig() {}
    public static SlotConfig fixed(double widthPercent) {
        SlotConfig c = new SlotConfig();
        c.policy = Policy.FIXED;
        c.slotWidthPercent = widthPercent;
        return c;
    }
    public static SlotConfig nonuniform(List<Double> edgesAsc) {
        SlotConfig c = new SlotConfig();
        c.policy = Policy.NONUNIFORM;
        c.nonuniformEdges.addAll(edgesAsc);
        return c;
    }
    public static SlotConfig adaptive(double seedWidthPercent, int maxSlots) {
        SlotConfig c = new SlotConfig();
        c.policy = Policy.ADAPTIVE;
        c.slotWidthPercent = seedWidthPercent;
        c.maxSlots = maxSlots;
        return c;
    }
}

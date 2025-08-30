package ai.nektron.grownet.growth;

import ai.nektron.grownet.Layer;
import ai.nektron.grownet.Neuron;
import ai.nektron.grownet.Region;
import ai.nektron.grownet.SlotConfig;

import java.util.List;

/**
 * Growth heuristics. Conservative and best‑effort: methods are no‑ops unless
 * the GrowthPolicy enables them and pressure/cooldowns are satisfied.
 */
public final class GrowthEngine {

    private GrowthEngine() { }

    /**
     * If average slots per neuron is high and we are below max layer count,
     * add a small layer and wire it from the previous layer. Best‑effort only.
     */
    public static void maybeGrow(Region region, GrowthPolicy policy) {
        if (region == null || policy == null) return;
        if (!policy.isEnableLayerGrowth()) return;

        // Compute avg slots/neuron across region
        double totalSlots = 0.0;
        double totalNeurons = 0.0;
        final List<Layer> layers = region.getLayers();
        for (Layer l : layers) {
            for (Neuron n : l.getNeurons()) {
                totalSlots   += n.getSlots().size();
                totalNeurons += 1.0;
            }
        }
        if (totalNeurons <= 0.0) return;
        final double avgSlots = totalSlots / totalNeurons;

        if (avgSlots < policy.getAvgSlotsThreshold()) return;
        if (layers.size() >= policy.getMaxLayers()) return;

        // cooldown via first layer's bus tick (if available); fallback to 0
        long tick = 0L;
        if (!layers.isEmpty()) {
            try { tick = layers.get(0).getBus().getCurrentStep(); } catch (Throwable ignored) { }
        }
        if ((tick - policy.getLastLayerGrowthTick()) < policy.getLayerCooldownTicks()) return;

        // Add a tiny excitatory-only layer and wire from previous layer with p=1.0
        final int prev = layers.size() - 1;
        final int newIndex = region.addLayer(/*excitatory*/ Math.max(1, (int)Math.round(Math.min(8, totalNeurons / Math.max(1.0, layers.size())))), 0, 0);
        if (prev >= 0) {
            region.connectLayers(prev, newIndex, 1.0, false);
        }
        policy.setLastLayerGrowthTick(tick);
    }

    /**
     * Scan for temporal‑focus outliers vs. per‑neuron anchor. If a large delta%% is
     * observed, mark the neuron by setting a short focus lock. Conservative: no graph
     * mutation by default; callers can use this as a hook point.
     */
    public static void maybeGrowNeurons(Region region, GrowthPolicy policy) {
        if (region == null || policy == null) return;
        if (!policy.isEnableNeuronGrowth()) return;

        final List<Layer> layers = region.getLayers();
        long tick = 0L;
        if (!layers.isEmpty()) {
            try { tick = layers.get(0).getBus().getCurrentStep(); } catch (Throwable ignored) { }
        }
        if ((tick - policy.getLastNeuronGrowthTick()) < policy.getNeuronCooldownTicks()) return;

        for (Layer l : layers) {
            for (Neuron n : l.getNeurons()) {
                try {
                    // Access temporal focus fields via public/protected API
                    double anchor = 0.0;
                    boolean set = false;
                    try { anchor = n.getFocusAnchor(); set = (n.getSlots() != null); } catch (Throwable ignored) { }

                    // derive epsilon and bin width from a default SlotConfig; best‑effort
                    SlotConfig cfg = new SlotConfig();
                    double denom = Math.max(Math.abs(anchor), cfg.getEpsilonScale());
                    double last = 0.0;
                    boolean haveLast = false;
                    try { last = n.getLastInputValue(); haveLast = true; } catch (Throwable ignored) { }
                    if (!set || !haveLast) continue;
                    double deltaPct = Math.abs(last - anchor) / (denom <= 0.0 ? 1e-6 : denom) * 100.0;
                    if (deltaPct >= policy.getNeuronOutlierThresholdPct()) {
                        // Lock briefly to avoid repeated triggers; reflection‑safe attempt
                        try {
                            java.lang.reflect.Field f = n.getClass().getDeclaredField("focusLockUntilTick");
                            f.setAccessible(true);
                            long lockUntil = tick + Math.max(1, policy.getNeuronCooldownTicks() / 4);
                            f.setLong(n, lockUntil);
                        } catch (Throwable ignored) { /* optional field */ }
                    }
                } catch (Throwable ignored) { /* best‑effort only */ }
            }
        }
        policy.setLastNeuronGrowthTick(tick);
    }
}

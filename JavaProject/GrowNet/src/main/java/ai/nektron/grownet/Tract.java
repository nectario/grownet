package ai.nektron.grownet;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

/**
 * A bundle of cross‑layer edges (white‑matter‑like). It registers a fire‑hook on each
 * source neuron. When sources fire, edges are reinforced and successful edges enqueue
 * deliveries. The Region flushes the tract’s queue once per tick (Phase B).
 */
public final class Tract {
    private final Layer source;
    private final Layer destination;
    private final RegionBus regionBus;
    private final boolean feedback;

    // edges[src] -> list of inter‑layer edges
    private final Map<Neuron, List<InterLayerEdge>> edges = new HashMap<>();
    private final List<QueuedEvent> queue = new ArrayList<>();
    private final Set<Neuron> hookedSources = new HashSet<>();

    public Tract(Layer source, Layer destination, RegionBus regionBus, boolean feedback) {
        this.source = source;
        this.destination = destination;
        this.regionBus = regionBus;
        this.feedback = feedback;
    }

    /** Randomly connect neurons from source to destination. */
    public void wireDenseRandom(double probability) {
        if (probability <= 0.0) return;

        for (Neuron src : source.getNeurons()) {
            for (Neuron dst : destination.getNeurons()) {
                if (src == dst) continue;
                if (ThreadLocalRandom.current().nextDouble() >= probability) continue;

                edges.computeIfAbsent(src, k -> new ArrayList<>())
                        .add(new InterLayerEdge(dst, feedback));
                if (!hookedSources.contains(src)) {
                    src.registerFireHook(makeSourceHook(src));
                    hookedSources.add(src);
                }
            }
        }
    }

    private FireHook makeSourceHook(Neuron src) {
        return (inputValue, self) -> {
            if (self != src) return;
            List<InterLayerEdge> list = edges.get(src);
            if (list == null || list.isEmpty()) return;

            for (InterLayerEdge e : list) {
                e.weight.reinforce(regionBus.getModulationFactor(), regionBus.getInhibitionFactor());
                boolean fired = e.weight.updateThreshold(inputValue);
                if (fired) {
                    queue.add(new QueuedEvent(e.target, inputValue));
                    e.lastStep = regionBus.getCurrentStep();
                }
            }
        };
    }

    /** Deliver queued events once (Phase B). Returns number of deliveries. */
    public int flush() {
        if (queue.isEmpty()) return 0;
        List<QueuedEvent> pending = new ArrayList<>(queue);
        queue.clear();
        int delivered = 0;
        for (QueuedEvent ev : pending) {
            ev.target.onInput(ev.value);
            delivered++;
        }
        return delivered;
    }

    /** Remove edges that are both stale and weak. Returns number pruned. */
    public int pruneEdges(long staleWindow, double minStrength) {
        int pruned = 0;
        Map<Neuron, List<InterLayerEdge>> keep = new HashMap<>();
        for (Map.Entry<Neuron, List<InterLayerEdge>> entry : edges.entrySet()) {
            List<InterLayerEdge> kept = new ArrayList<>();
            for (InterLayerEdge e : entry.getValue()) {
                boolean stale = (regionBus.getCurrentStep() - e.lastStep) > staleWindow;
                boolean weak  = e.weight.getStrengthValue() < minStrength;
                if (stale && weak) pruned++; else kept.add(e);
            }
            if (!kept.isEmpty()) keep.put(entry.getKey(), kept);
        }
        edges.clear();
        edges.putAll(keep);
        return pruned;
    }

    // --- helpers ---

    private static final class QueuedEvent {
        final Neuron target;
        final double value;
        QueuedEvent(Neuron target, double value) { this.target = target; this.value = value; }
    }

    private static final class InterLayerEdge {
        final Neuron target;
        final Weight weight = new Weight();
        final boolean feedback;
        long lastStep = 0L;

        InterLayerEdge(Neuron target, boolean feedback) {
            this.target = target;
            this.feedback = feedback;
        }
    }
}

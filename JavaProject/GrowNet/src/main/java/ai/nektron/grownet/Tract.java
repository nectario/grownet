package ai.nektron.grownet;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Bundle of cross-layer edges with a per-tick delivery queue.
 * Sources register a fire-hook so successful edges enqueue events.
 * Region flushes each tract once per tick (Phase B).
 */
public final class Tract {

    private final Layer source;
    private final Layer destination;
    private final RegionBus regionBus;
    private final boolean feedback;

    // Inter-layer edges: source neuron -> list of edges
    private final Map<Neuron, List<InterLayerEdge>> edges = new HashMap<>();

    // Per-tick queue of deliveries
    private final List<QueuedEvent> queue = new ArrayList<>();

    // Prevent double hook registration per source neuron
    private final Set<Neuron> hookedSources = new HashSet<>();

    public Tract(Layer source, Layer destination, RegionBus regionBus, boolean feedback) {
        this.source = source;
        this.destination = destination;
        this.regionBus = regionBus;
        this.feedback = feedback;
    }

    /**
     * Dense random wiring between source and destination layers.
     * Every created edge is tagged with the tract-level "feedback" flag.
     */
    public void wireDenseRandom(double probability) {
        if (probability <= 0.0) return;

        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (Neuron src : source.getNeurons()) {
            for (Neuron dst : destination.getNeurons()) {
                if (src == dst) continue;                       // never self-edge across layers
                if (rnd.nextDouble() >= probability) continue;

                edges.computeIfAbsent(src, k -> new ArrayList<>())
                        .add(new InterLayerEdge(dst, feedback));

                // Install one fire-hook per source neuron (idempotent)
                if (!hookedSources.contains(src)) {
                    src.registerFireHook(makeSourceHook(src));
                    hookedSources.add(src);
                }
            }
        }
    }

    /**
     * Build a fire-hook bound to a specific source neuron.
     * On each source spike, reinforce and gate edges; enqueue events for fired edges.
     */
    private FireHook makeSourceHook(Neuron src) {
        return (inputValue, self) -> {
            if (self != src) return;

            List<InterLayerEdge> list = edges.get(src);
            if (list == null || list.isEmpty()) return;

            for (InterLayerEdge e : list) {
                // Local learning on the edge (bounded reinforcement)
                e.weight.reinforce(regionBus.getModulationFactor(), regionBus.getInhibitionFactor());

                // Threshold update + gate (T0 + T2 hybrid)
                boolean fired = e.weight.updateThreshold(inputValue);
                if (fired) {
                    queue.add(new QueuedEvent(e.target, inputValue));
                    e.lastStep = regionBus.getCurrentStep();
                }
            }
        };
    }

    public int flush() {
        if (queue.isEmpty()) return 0;
        int delivered = 0;
        List<QueuedEvent> pending = new ArrayList<>(queue);
        queue.clear();

        for (QueuedEvent ev : pending) {
            boolean fired = ev.target.isFiredLast();
            if (fired) {
                ev.target.onOutput(ev.value);
                if (!(ev.target instanceof OutputNeuron)) {  // keep actuator boundary
                    ev.target.fire(ev.value);
                }
                delivered++;
            }
        }
        return delivered;
    }


    /**
     * Remove edges that are both stale and weak. Returns number pruned.
     */
    public int pruneEdges(long staleWindow, double minStrength) {
        int pruned = 0;
        Map<Neuron, List<InterLayerEdge>> keep = new HashMap<>();

        for (Map.Entry<Neuron, List<InterLayerEdge>> entry : edges.entrySet()) {
            List<InterLayerEdge> kept = new ArrayList<>();
            for (InterLayerEdge e : entry.getValue()) {
                boolean stale = (regionBus.getCurrentStep() - e.lastStep) > staleWindow;
                boolean weak  = e.weight.getStrengthValue() < minStrength;
                if (stale && weak) {
                    pruned++;
                } else {
                    kept.add(e);
                }
            }
            if (!kept.isEmpty()) {
                keep.put(entry.getKey(), kept);
            }
        }
        edges.clear();
        edges.putAll(keep);
        return pruned;
    }

    // ---------- Helpers ----------

    private static final class QueuedEvent {
        final Neuron target;
        final double value;

        QueuedEvent(Neuron target, double value) {
            this.target = target;
            this.value = value;
        }
    }

    private static final class InterLayerEdge {
        final Neuron target;
        final Weight weight = new Weight();
        final boolean feedback;
        long lastStep = 0;

        InterLayerEdge(Neuron target, boolean feedback) {
            this.target = target;
            this.feedback = feedback;
        }
    }
}

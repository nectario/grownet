package ai.nektron.grownet;

import java.util.*;

/**
 * Inter-layer projection. Sources register fire hooks that enqueue events.
 * flush() delivers the queued events to destination neurons in a single batch.
 */
public class Tract {
    private final Layer source;
    private final Layer destination;
    private final RegionBus regionBus;
    private final boolean feedback;

    private final List<Edge> edges = new ArrayList<>();
    private final Queue<Event> queue = new ArrayDeque<>();
    private final Random random = new Random();

    private static class Edge {
        final Neuron sourceNeuron;
        final Neuron targetNeuron;
        final Weight weight = new Weight();
        long lastStep = 0L;
        Edge(Neuron s, Neuron t) { this.sourceNeuron = s; this.targetNeuron = t; }
    }

    private static class Event {
        final Neuron targetNeuron;
        final double amplitude;
        Event(Neuron target, double amp) { this.targetNeuron = target; this.amplitude = amp; }
    }

    public Tract(Layer source, Layer destination, RegionBus bus, boolean feedback) {
        this.source = source;
        this.destination = destination;
        this.regionBus = bus;
        this.feedback = feedback;
        // Register hooks on all current source neurons
        for (Neuron n : source.getNeurons()) {
            n.registerFireHook((value, who) -> onSourceFired(who, value));
        }
    }

    public void wireDenseRandom(double probability) {
        List<Neuron> s = source.getNeurons();
        List<Neuron> d = destination.getNeurons();
        for (Neuron sn : s) {
            for (Neuron dn : d) {
                if (random.nextDouble() < probability) {
                    edges.add(new Edge(sn, dn));
                }
            }
        }
    }

    private void onSourceFired(Neuron who, double amplitude) {
        // For all edges whose source is 'who', enqueue delivery
        for (Edge e : edges) {
            if (e.sourceNeuron == who) {
                e.weight.reinforce(regionBus.getModulationScale(), regionBus.getInhibitionFactor());
                e.lastStep = regionBus.getCurrentStep();
                if (e.weight.updateThreshold(amplitude)) {
                    queue.add(new Event(e.targetNeuron, amplitude));
                }
            }
        }
    }

    /** Deliver queued events once. Returns number of delivered events. */
    public int flush() {
        int delivered = 0;
        while (!queue.isEmpty()) {
            Event ev = queue.poll();
            ev.targetNeuron.onInput(ev.amplitude);
            delivered++;
        }
        return delivered;
    }

    /** Prune weak or stale edges. */
    public int pruneEdges(long staleWindow, double minStrength) {
        int before = edges.size();
        edges.removeIf(e -> (regionBus.getCurrentStep() - e.lastStep) > staleWindow
                && e.weight.getStrength() < minStrength);
        return before - edges.size();
    }
}
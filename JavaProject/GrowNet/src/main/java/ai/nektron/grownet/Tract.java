package ai.nektron.grownet;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Random;
import java.util.function.BiConsumer;

/**
 * Inter-layer projection.
 * Sources register fire-hooks that enqueue events.
 * flush() delivers the queued events to destination neurons in a single batch.
 */
public final class Tract {

    private final Layer source;
    private final Layer destination;
    private final RegionBus regionBus;
    private final boolean feedback;

    private final List<Edge> edges = new ArrayList<>();
    private final Deque<Event> queue = new ArrayDeque<>();
    private final Random rng = new Random();

    /** A static snapshot of a connection between two neurons. */
    private static final class Edge {
        final Neuron sourceNeuron;
        final Neuron targetNeuron;
        long lastStep = 0L;
        Edge(Neuron s, Neuron t) { this.sourceNeuron = s; this.targetNeuron = t; }
    }

    /** A queued delivery to a target neuron. */
    private static final class Event {
        final Neuron targetNeuron;
        final double amplitude;
        Event(Neuron target, double amp) { this.targetNeuron = target; this.amplitude = amp; }
    }

    public Tract(Layer source, Layer destination, RegionBus bus, boolean feedback) {
        this.source = source;
        this.destination = destination;
        this.regionBus = bus;
        this.feedback = feedback;

        // Register hooks on all current source neurons.
        BiConsumer<Double, Neuron> hook = (value, who) -> onSourceFired(who, value);
        for (Neuron neuron : source.getNeurons()) {
            neuron.registerFireHook(hook);
        }
    }

    /**
     * Randomly connect every neuron in source layer to neurons in destination layer with
     * probability p. (If {@code feedback} is true, the created edges are still the same;
     * your Neuron.connect handles any feedback semantics.)
     * @return number of edges created
     */
    public int wireDenseRandom(double probability) {
        int edgesCreated = 0;
        List<Neuron> src = source.getNeurons();
        List<Neuron> dst = destination.getNeurons();

        for (Neuron a : src) {
            for (Neuron b : dst) {
                if (rng.nextDouble() < probability) {
                    edges.add(new Edge(a, b));
                    edgesCreated++;
                    // a.connect(b, feedback) — optional, if you mirror adjacency elsewhere
                }
            }
        }
        return edgesCreated;
    }

    /** Fire-hook: batch an event for each edge whose source == who. */
    private void onSourceFired(Neuron who, double amplitude) {
        for (Edge e : edges) {
            if (e.sourceNeuron == who) {
                e.lastStep = regionBus.getCurrentStep();
                queue.add(new Event(e.targetNeuron, amplitude));
            }
        }
    }

    /**
     * Deliver queued events to target neurons.
     * @return number of target neurons that actually fired (best‑effort metric).
     */
    public int flush() {
        int delivered = 0;
        while (!queue.isEmpty()) {
            Event ev = queue.poll();
            boolean fired = ev.targetNeuron.onInput(ev.amplitude); // learning + threshold are inside the neuron
            if (fired) delivered++;
        }
        return delivered;
    }

    /**
     * Prune stale edges.
     * NOTE: now that weights live inside target neurons, {@code minStrength} is ignored
     * here (we do not have a per-edge weight). We keep the parameter for API symmetry.
     *
     * @return number of edges removed
     */
    public int pruneEdges(long staleWindow, double /*unused*/ minStrength) {
        final long now = regionBus.getCurrentStep();
        int before = edges.size();
        edges.removeIf(e -> (now - e.lastStep) > staleWindow);
        return before - edges.size();
    }

    // ------------ accessors (optional helpers) ----------------

    public Layer getSource()      { return source; }
    public Layer getDestination() { return destination; }
    public boolean isFeedback()   { return feedback; }
    public int edgeCount()        { return edges.size(); }
}

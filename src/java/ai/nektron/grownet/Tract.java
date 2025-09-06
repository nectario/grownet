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
    
    // Optional windowed-wiring helpers
    private final java.util.Set<Integer> allowedSources;
    private final java.util.Map<Integer, Integer> centerIndexBySource;

    private final List<Edge> edges = new ArrayList<>();
    private final Deque<Event> queue = new ArrayDeque<>();
    private final Random rng = new Random();

    /** A static snapshot of a connection between two neurons. */
    private static final class Edge {
        final Neuron sourceNeuron;
        final Neuron targetNeuron;
        long lastStep = 0L;
        Edge(Neuron source, Neuron target) { this.sourceNeuron = source; this.targetNeuron = target; }
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
        this.allowedSources = java.util.Collections.emptySet();
        this.centerIndexBySource = java.util.Collections.emptyMap();

        // Register hooks on all current source neurons.
        BiConsumer<Double, Neuron> hook = (value, who) -> onSourceFired(who, value);
        for (Neuron neuron : source.getNeurons()) {
            neuron.registerFireHook(hook);
        }
    }

    /** Windowed-wiring constructor: restrict to allowed sources and optional center mapping. */
    public Tract(
            Layer source,
            Layer destination,
            RegionBus bus,
            boolean feedback,
            java.util.Set<Integer> allowedSources,
            java.util.Map<Integer, Integer> centerIndexBySource) {
        this.source = source;
        this.destination = destination;
        this.regionBus = bus;
        this.feedback = feedback;
        this.allowedSources = (allowedSources == null ? java.util.Collections.emptySet() : new java.util.HashSet<>(allowedSources));
        this.centerIndexBySource = (centerIndexBySource == null ? java.util.Collections.emptyMap() : new java.util.HashMap<>(centerIndexBySource));

        // Subscribe only the allowed subset (or all if empty)
        for (int i = 0; i < source.getNeurons().size(); ++i) {
            if (this.allowedSources.isEmpty() || this.allowedSources.contains(i)) {
                final int srcIdx = i;
                source.getNeurons().get(i).registerFireHook((value, who) -> onSourceFiredIndex(srcIdx, value));
            }
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

        for (Neuron sourceNeuron : src) {
            for (Neuron targetNeuron : dst) {
                if (rng.nextDouble() < probability) {
                    edges.add(new Edge(sourceNeuron, targetNeuron));
                    edgesCreated++;
                    // sourceNeuron.connect(targetNeuron, feedback) — optional, if you mirror adjacency elsewhere
                }
            }
        }
        return edgesCreated;
    }

    /** Fire-hook: batch an event for each edge whose source == who. */
    private void onSourceFired(Neuron who, double amplitude) {
        // Windowed: if we have a center mapping, prefer direct delivery path
        if (!centerIndexBySource.isEmpty() || !allowedSources.isEmpty()) {
            // Without the index we cannot map; fall back to fan-out
            for (Neuron target : destination.getNeurons()) {
                boolean fired = target.onInput(amplitude);
                if (fired) try { target.onOutput(amplitude); } catch (Throwable ignored) {}
            }
            return;
        }
        for (Edge edge : edges) {
            if (edge.sourceNeuron == who) {
                edge.lastStep = regionBus.getCurrentStep();
                queue.add(new Event(edge.targetNeuron, amplitude));
            }
        }
    }

    /** Windowed path: we already know the source index. */
    private void onSourceFiredIndex(int sourceIndex, double amplitude) {
        if (!centerIndexBySource.isEmpty()) {
            Integer centerIndex = centerIndexBySource.get(sourceIndex);
            if (centerIndex != null && centerIndex >= 0 && centerIndex < destination.getNeurons().size()) {
                Neuron centerNeuron = destination.getNeurons().get(centerIndex);
                boolean fired = centerNeuron.onInput(amplitude);
                if (fired) try { centerNeuron.onOutput(amplitude); } catch (Throwable ignored) {}
            }
            return;
        }
        // Generic: fan-out to all neurons in dest
        for (Neuron target : destination.getNeurons()) {
            boolean fired = target.onInput(amplitude);
            if (fired) try { target.onOutput(amplitude); } catch (Throwable ignored) {}
        }
    }

    /**
     * Deliver queued events to target neurons.
     * @return number of target neurons that actually fired (best‑effort metric).
     */
    public int flush() {
        int delivered = 0;
        while (!queue.isEmpty()) {
            Event event = queue.poll();
            boolean fired = event.targetNeuron.onInput(event.amplitude); // learning + threshold are inside the neuron
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

    /**
     * Subscribe a newly created source neuron so its spikes propagate through this tract.
     * This helper is best-effort and only registers a fire hook; it does not create new edges.
     */
    public void attachSourceNeuron(int newSourceIndex) {
        if (source == null || destination == null) return;
        if (!allowedSources.isEmpty() && !allowedSources.contains(newSourceIndex)) return;
        final List<Neuron> src = source.getNeurons();
        if (newSourceIndex < 0 || newSourceIndex >= src.size()) return;
        src.get(newSourceIndex).registerFireHook((amplitude, who) -> onSourceFiredIndex(newSourceIndex, amplitude));
    }
}

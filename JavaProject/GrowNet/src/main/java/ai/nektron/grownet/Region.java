package ai.nektron.grownet;

import java.util.*;

/**
 * A named group of layers and tracts with a two‑phase tick schedule.
 * Phase A: deliver external input to entry layers (intra‑layer propagation).
 * Phase B: flush inter‑layer tracts once. Then decay region/layer buses.
 */
public final class Region {
    private final String name;
    private final List<Layer> layers = new ArrayList<>();
    private final List<Tract> tracts = new ArrayList<>();
    private final RegionBus bus = new RegionBus();
    private final Map<String, List<Integer>> inputPorts = new HashMap<>();
    private final Map<String, List<Integer>> outputPorts = new HashMap<>();

    public Region(String name) { this.name = name; }

    // ----- construction -----

    public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
        layers.add(layer);
        return layers.size() - 1;
    }

    public Tract connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) {
        Layer src = layers.get(sourceIndex);
        Layer dst = layers.get(destIndex);
        Tract tract = new Tract(src, dst, bus, feedback);
        tract.wireDenseRandom(probability);
        tracts.add(tract);
        return tract;
    }

    public void bindInput(String port, List<Integer> layerIndices) {
        inputPorts.put(port, new ArrayList<>(layerIndices));
    }

    public void bindOutput(String port, List<Integer> layerIndices) {
        outputPorts.put(port, new ArrayList<>(layerIndices));
    }

    // ----- region control -----

    public void pulseInhibition(double factor) { bus.setInhibitionFactor(factor); }
    public void pulseModulation(double factor) { bus.setModulationFactor(factor); }

    // ----- main loop -----

    public RegionMetrics tick(String port, double value) {
        // Phase A: external input
        List<Integer> entries = inputPorts.getOrDefault(port, Collections.emptyList());
        for (int idx : entries) {
            layers.get(idx).forward(value);
        }

        // Phase B: inter‑layer propagation
        int delivered = 0;
        for (Tract t : tracts) {
            delivered += t.flush();
        }

        // Decay
        for (Layer l : layers) l.getBus().decay();
        bus.decay();

        // Light metrics
        int totalSlots = 0;
        int totalSynapses = 0;
        for (Layer l : layers) {
            for (Neuron n : l.getNeurons()) {
                totalSlots   += n.getSlots().size();
                totalSynapses += n.getOutgoing().size();
            }
        }
        return new RegionMetrics(delivered, totalSlots, totalSynapses);
    }

    /** Prune weak+stale synapses inside layers and edges inside tracts. */
    public PruneSummary prune(long synapseStaleWindow, double synapseMinStrength,
                              long tractStaleWindow, double tractMinStrength) {
        int prunedSynapses = 0;
        for (Layer l : layers) {
            for (Neuron n : l.getNeurons()) {
                int before = n.getOutgoing().size();
                n.pruneSynapses(bus.getCurrentStep(), synapseStaleWindow, synapseMinStrength);
                prunedSynapses += before - n.getOutgoing().size();
            }
        }
        int prunedEdges = 0;
        for (Tract t : tracts) prunedEdges += t.pruneEdges(tractStaleWindow, tractMinStrength);
        return new PruneSummary(prunedSynapses, prunedEdges);
    }

    public PruneSummary prune() {
        return prune(10_000L, 0.05, 10_000L, 0.05);
    }

    // Getters
    public String getName()               { return name; }
    public List<Layer> getLayers()        { return layers; }
    public List<Tract> getTracts()        { return tracts; }
    public RegionBus getBus()             { return bus; }
    public Map<String, List<Integer>> getInputPorts() { return inputPorts; }

    // Simple metric records (Java 16+; works with your Java 21 pom)
    public record RegionMetrics(int deliveredEvents, int totalSlots, int totalSynapses) {}
    public record PruneSummary(int prunedSynapses, int prunedEdges) {}
}

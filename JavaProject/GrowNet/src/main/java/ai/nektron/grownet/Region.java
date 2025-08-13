package ai.nektron.grownet;

import java.util.*;

/** Region = a set of layers plus directed tracts between them. */
public class Region {
    public static class RegionMetrics {
        public int deliveredEvents;
        public int totalSlots;
        public int totalSynapses;
    }
    public static class PruneSummary {
        public int prunedSynapses;
        public int prunedEdges;
    }

    private final String name;
    private final RegionBus bus = new RegionBus();
    private final List<Layer> layers = new ArrayList<>();
    private final List<Tract> tracts = new ArrayList<>();
    private final Map<String, List<Integer>> inputPorts = new HashMap<>();
    private final Map<String, List<Integer>> outputPorts = new HashMap<>();

    public Region(String name) { this.name = name; }

    public int addLayer(int excitatory, int inhibitory, int modulatory) {
        Layer layer = new Layer(excitatory, inhibitory, modulatory);
        layers.add(layer);
        return layers.size() - 1;
    }

    public Tract connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) {
        Layer src = layers.get(sourceIndex);
        Layer dst = layers.get(destIndex);
        Tract t = new Tract(src, dst, bus, feedback);
        t.wireDenseRandom(probability);
        tracts.add(t);
        return t;
    }

    public void bindInput(String port, List<Integer> layerIndices) {
        inputPorts.put(port, new ArrayList<>(layerIndices));
    }

    public void bindOutput(String port, List<Integer> layerIndices) {
        outputPorts.put(port, new ArrayList<>(layerIndices));
    }

    public RegionMetrics tick(String port, double value) {
        // Phase A: external input to entry layers
        List<Integer> indices = inputPorts.get(port);
        if (indices != null) {
            for (int idx : indices) layers.get(idx).forward(value);
        }
        // Phase B: inter-layer deliveries
        int delivered = 0;
        for (Tract t : tracts) delivered += t.flush();
        // Decay buses
        for (Layer l : layers) l.getBus().decay();
        bus.decay();
        // Metrics
        RegionMetrics m = new RegionMetrics();
        m.deliveredEvents = delivered;
        for (Layer l : layers) {
            for (Neuron n : l.getNeurons()) {
                m.totalSlots += n.getSlots().size();
                m.totalSynapses += n.getOutgoing().size();
            }
        }
        return m;
    }

    public PruneSummary prune(long synapseStaleWindow, double synapseMinStrength,
                              long tractStaleWindow,   double tractMinStrength) {
        PruneSummary s = new PruneSummary();
        for (Layer l : layers) {
            for (Neuron n : l.getNeurons()) {
                int before = n.getOutgoing().size();
                n.pruneSynapses(bus.getCurrentStep(), synapseStaleWindow, synapseMinStrength);
                s.prunedSynapses += (before - n.getOutgoing().size());
            }
        }
        for (Tract t : tracts) s.prunedEdges += t.pruneEdges(tractStaleWindow, tractMinStrength);
        return s;
    }

    public String getName() { return name; }
    public List<Layer> getLayers() { return layers; }
    public List<Tract> getTracts() { return tracts; }
    public RegionBus getBus() { return bus; }
}
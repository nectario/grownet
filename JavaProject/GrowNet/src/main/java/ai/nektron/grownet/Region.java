package ai.nektron.grownet;

import java.util.*;

public final class Region {
    public static final class Metrics {
        public int deliveredEvents;
        public int totalSlots;
        public int totalSynapses;
    }
    public static final class PruneSummary {
        public int prunedSynapses;
        public int prunedEdges;
    }

    private final String name;
    private final LateralBus bus = new LateralBus();
    private final List<Layer> layers = new ArrayList<>();
    private final Map<String, List<Integer>> inputPorts = new HashMap<>();

    private final SlotConfig defaultCfg;

    public Region(String name, SlotConfig defaultCfg) {
        this.name = name;
        this.defaultCfg = defaultCfg;
    }

    public int addLayer(int excitatory, int inhibitory, int modulatory) {
        layers.add(new Layer(excitatory, inhibitory, modulatory, defaultCfg));
        return layers.size() - 1;
    }

    public void bindInput(String port, List<Integer> layerIndices) {
        inputPorts.put(port, layerIndices);
    }

    public Metrics tick(String port, double value) {
        List<Integer> idxs = inputPorts.get(port);
        if (idxs != null) {
            for (int i : idxs) layers.get(i).forward(value);
        }
        for (Layer l : layers) l.decay();
        bus.decay();

        Metrics m = new Metrics();
        for (Layer l : layers) {
            for (Neuron n : l.neurons()) {
                m.totalSlots += n.slots().size();
                m.totalSynapses += n.outgoing().size();
            }
        }
        return m;
    }

    public PruneSummary prune(long synapseStaleWindow,
                              double synapseMinStrength) {
        // Wiring/graph pruning lives in Tract; keep simple summary for now.
        PruneSummary ps = new PruneSummary();
        ps.prunedSynapses = 0;
        ps.prunedEdges = 0;
        return ps;
    }

    public List<Layer> layers() { return layers; }
    public LateralBus bus() { return bus; }
    public String name() { return name; }
}

package ai.nektron.grownet;

import java.util.*;

public final class Region {

    // ---------- public nested types ----------
    public static final class Metrics {
        public int deliveredEvents = 0;  // best-effort placeholder unless Layers/Neurons report explicitly
        public int totalSlots      = 0;
        public int totalSynapses   = 0;
    }

    public static final class PruneSummary {
        public int prunedSynapses = 0;
        public int prunedEdges    = 0;   // reserved for future inter-layer tract pruning
    }

    // ---------- fields ----------
    private final String name;
    private final List<Layer> layers = new ArrayList<>();
    private final Map<String, List<Integer>> inputPorts  = new HashMap<>();
    private final Map<String, List<Integer>> outputPorts = new HashMap<>();
    private final RegionBus bus = new RegionBus();
    private final Random rng = new Random(1234);

    // ---------- construction ----------
    public Region(String name) { this.name = name; }

    // addLayer / connectLayers / bindInput ... (unchanged) --------------------

    // ---------- tick: scalar ----------
    public Metrics tick(String port, double value) {
        Metrics m = new Metrics();

        List<Integer> entry = inputPorts.get(port);
        if (entry != null) {
            for (int layerIndex : entry) {
                layers.get(layerIndex).forward(value);
                m.deliveredEvents += 1;       // lightweight placeholder
            }
        }

        // end-of-tick housekeeping for all layers
        for (Layer layer : layers) layer.endTick();

        // simple aggregate metrics for dashboards
        for (Layer layer : layers) {
            for (Neuron neuron : layer.getNeurons()) {
                m.totalSlots    += neuron.getSlots().size();
                m.totalSynapses += neuron.getOutgoing().size();
            }
        }
        return m;
    }

    // ---------- tick: image frame (NEW) ----------
    public Metrics tickImage(String port, double[][] frame) {
        Metrics m = new Metrics();

        List<Integer> entry = inputPorts.get(port);
        if (entry != null) {
            for (int layerIndex : entry) {
                Layer layer = layers.get(layerIndex);
                if (layer instanceof InputLayer2D) {
                    ((InputLayer2D) layer).forwardImage(frame);
                    m.deliveredEvents += 1;    // per entry layer; keep it lightweight
                } else {
                    // Fallback: if someone bound a non-image layer to this port,
                    // you could forward an average or skip. We skip by design.
                }
            }
        }

        // end-of-tick housekeeping
        for (Layer layer : layers) layer.endTick();

        // aggregates
        for (Layer layer : layers) {
            for (Neuron neuron : layer.getNeurons()) {
                m.totalSlots    += neuron.getSlots().size();
                m.totalSynapses += neuron.getOutgoing().size();
            }
        }
        return m;
    }

    // ---------- accessors ----------
    public String getName() { return name; }
    public List<Layer> getLayers() { return layers; }
    public RegionBus getBus() { return bus; }

    // ---------- wiring helpers already present ----------
    // int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) { ... }
    // int connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) { ... }
    // void bindInput(String port, List<Integer> layerIndices) { ... }
    // void bindOutput(String port, List<Integer> layerIndices) { ... }

    // ---------- prune(...) remains unchanged ----------
}

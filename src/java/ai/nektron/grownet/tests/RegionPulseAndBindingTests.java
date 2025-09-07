package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.LateralBus;
import ai.nektron.grownet.metrics.RegionMetrics;
import java.util.List;

public class RegionPulseAndBindingTests {

    private static void check(boolean cond, String msg) {
        if (!cond) throw new RuntimeException("Test failed: " + msg);
    }

    /** Multi-layer input binding should increment deliveredEvents once per bound entry layer. */
    private static void testMultiLayerInputBinding() {
        Region region = new Region("t");
        int l0 = region.addLayer(1, 0, 0);
        int l1 = region.addLayer(1, 0, 0);
        region.bindInput("x", List.of(l0, l1));
        RegionMetrics m = region.tick("x", 1.0);
        System.out.println("[JAVA] multiLayerBinding delivered=" + m.getDeliveredEvents());
        check(m.getDeliveredEvents() == 2, "deliveredEvents should equal number of bound entry layers");
    }

    /** Pulses: simulate by setting bus factors prior to tick; expect decay/reset after tick. */
    private static void testPulseChecks() {
        Region region = new Region("t");
        int l0 = region.addLayer(1, 0, 0);
        region.bindInput("x", List.of(l0));

        // Access the layer bus directly (Java Region does not expose pulse*).
        LateralBus bus = region.getLayers().get(l0).getBus();
        bus.setModulationFactor(1.5);
        bus.setInhibitionFactor(0.7);

        RegionMetrics m = region.tick("x", 0.5);
        System.out.println("[JAVA] pulseChecks -> " + m + "  post(mod=" +
                bus.getModulationFactor() + ", inh=" + bus.getInhibitionFactor() + ")");

        // Java LateralBus.decay() resets modulation=1.0 and inhibition=0.0 each tick.
        check(Math.abs(bus.getModulationFactor() - 1.0) < 1e-12, "modulation must reset to 1.0");
        check(Math.abs(bus.getInhibitionFactor() - 0.0) < 1e-12, "inhibition must reset to 0.0");
    }

    public static void main(String[] args) {
        testMultiLayerInputBinding();
        testPulseChecks();
        System.out.println("[JAVA] RegionPulseAndBindingTests passed.");
    }
}

package ai.nektron.grownet.tests;

import ai.nektron.grownet.Layer;
import ai.nektron.grownet.Neuron;
import ai.nektron.grownet.Region;
import ai.nektron.grownet.policy.DeterministicLayout;
import ai.nektron.grownet.policy.ProximityConfig;
import ai.nektron.grownet.policy.ProximityEngine;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class ProximityPolicyTests {

    @Test
    public void stepModeBudgetAndCooldown() {
        Region region = new Region("prox-step");
        int layerIndex = region.addLayer(9, 0, 0);

        ProximityConfig cfg = new ProximityConfig()
                .setEnabled(true)
                .setFunction("STEP")
                .setRadius(1.25)
                .setMaxEdgesPerTick(5)
                .setCooldownTicks(100);

        int added = ProximityEngine.apply(region, cfg);
        assertTrue(added >= 0 && added <= 5);

        // Cooldown prevents immediate re-application on the same neurons
        int addedSecond = ProximityEngine.apply(region, cfg);
        assertEquals(0, addedSecond);

        // Sanity: at least some neurons should now have outgoing edges
        Layer layer = region.getLayers().get(l);
        boolean any = false;
        for (Neuron n : layer.getNeurons()) {
            if (!n.getOutgoing().isEmpty()) { any = true; break; }
        }
        assertTrue(any, "expected some proximity edges after STEP application");
    }
}

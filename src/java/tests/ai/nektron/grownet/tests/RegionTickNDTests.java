package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class RegionTickNDTests {
    @Test
    public void ndTickDeliversOneEvent() {
        Region region = new Region("nd-basic");
        int[] shape = new int[]{2, 3};
        region.bindInputND("nd", shape, 1.0, 0.01, List.of());
        double[] flat = new double[]{0, 0, 0, 0, 0, 0};
        var m = region.tickND("nd", flat, shape);
        assertEquals(1L, m.getDeliveredEvents());
    }
}


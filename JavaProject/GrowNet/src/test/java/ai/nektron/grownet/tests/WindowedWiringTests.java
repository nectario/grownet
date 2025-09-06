package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.InputLayer2D;
import ai.nektron.grownet.OutputLayer2D;

/**
 * Tiny smoke tests for Region.connectLayersWindowed(...).
 * Style matches other non-JUnit tests (manual checks + main()).
 */
public final class WindowedWiringTests {

    private static void check(boolean cond, String msg) {
        if (!cond) throw new RuntimeException("Test failed: " + msg);
    }

    private static void testValidKernelCoversAllSources() {
        final int H = 4, W = 4;
        Region region = new Region("windowed_valid");

        int inIdx  = region.addInputLayer2D(H, W, 1.0, 0.01);
        int hidIdx = region.addLayer(4, 0, 0);
        int outIdx = region.addOutputLayer2D(H, W, 0.2);

        // VALID padding, 2x2 kernel, stride 2 → non-overlapping windows; unique sources = H*W
        int wiresToOut = region.connectLayersWindowed(inIdx, outIdx, 2, 2, 2, 2, "valid", false);
        int wiresToHid = region.connectLayersWindowed(inIdx, hidIdx, 2, 2, 2, 2, "valid", false);

        int expected = H * W;
        System.out.println("[JAVA] windowed VALID → out unique=" + wiresToOut + ", hid unique=" + wiresToHid);
        check(wiresToOut == expected, "VALID to OutputLayer2D should subscribe all sources");
        check(wiresToHid == expected,  "VALID to hidden layer should subscribe all sources");
    }

    private static void testSameKernelCoversAllSources() {
        final int H = 4, W = 4;
        Region region = new Region("windowed_same");

        int inIdx  = region.addInputLayer2D(H, W, 1.0, 0.01);
        int outIdx = region.addOutputLayer2D(H, W, 0.2);

        // SAME padding, 2x2 kernel, stride 2 → union of clamped windows should still cover all sources
        int wires = region.connectLayersWindowed(inIdx, outIdx, 2, 2, 2, 2, "same", false);
        int expected = H * W;
        System.out.println("[JAVA] windowed SAME → out unique=" + wires);
        check(wires == expected, "SAME to OutputLayer2D should subscribe all sources");
    }

    public static void main(String[] args) {
        testValidKernelCoversAllSources();
        testSameKernelCoversAllSources();
        System.out.println("[JAVA] All WindowedWiringTests passed.");
    }
}


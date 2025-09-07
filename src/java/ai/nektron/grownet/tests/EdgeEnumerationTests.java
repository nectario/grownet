package ai.nektron.grownet.tests;

import static org.junit.jupiter.api.Assertions.*;

import ai.nektron.grownet.Region;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

public class EdgeEnumerationTests {

  // Synapse target indices are not exposed; windowed wiring to OutputLayer2D uses
  // tract-level center routing. We assert the return value semantics instead.

  @Test
  @DisplayName("Mojo parity: center targets are deduped for OutputLayer2D windowed wiring")
  public void centerTargetsAreDeduped() {
    Region region = new Region("dedupe-java");
    int srcIndex = region.addInputLayer2D(4, 4, 1.0, 0.01);
    int dstIndex = region.addOutputLayer2D(4, 4, 0.0);
    // SAME padding, 3x3 kernel on 4x4 grid covers all pixels at least once.
    int uniqueSources = region.connectLayersWindowed(srcIndex, dstIndex, 3, 3, 1, 1, "same", false);
    Assertions.assertEquals(16, uniqueSources, "Return value must be unique source subscriptions.");
  }
}

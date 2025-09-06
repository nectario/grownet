package ai.nektron.grownet;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import java.util.*;

public class EdgeEnumerationTests {

  private static Map<Integer, List<Integer>> enumerateEdgesOutput2D(Region region, int srcLayerIndex, int dstLayerIndex) {
    Map<Integer, List<Integer>> mapping = new HashMap<>();
    var srcLayer = region.getLayers().get(srcLayerIndex);
    var dstLayer = region.getLayers().get(dstLayerIndex);
    // Adjust these getters if your API differs:
    var neuronList = srcLayer.getNeurons();
    for (int sourceIndex = 0; sourceIndex < neuronList.size(); sourceIndex++) {
      var outgoing = neuronList.get(sourceIndex).getOutgoing();
      List<Integer> targets = new ArrayList<>();
      for (int synIndex = 0; synIndex < outgoing.size(); synIndex++) {
        // Adjust if Synapse exposes a different target getter:
        targets.add(outgoing.get(synIndex).getTargetIndex());
      }
      mapping.put(sourceIndex, targets);
    }
    return mapping;
  }

  @Test
  @DisplayName("Mojo parity: center targets are deduped for OutputLayer2D windowed wiring")
  public void centerTargetsAreDeduped() {
    Region region = new Region("dedupe-java");
    int srcIndex = region.addInput2DLayer(4, 4);     // adjust if your ctor name differs
    int dstIndex = region.addOutput2DLayer(4, 4);
    int uniqueSources = region.connectLayersWindowed(srcIndex, dstIndex, 3, 3, 1, 1, "same", false);
    assertEquals(16, uniqueSources, "All sources should participate at least once.");
    Map<Integer, List<Integer>> edges = enumerateEdgesOutput2D(region, srcIndex, dstIndex);
    for (Map.Entry<Integer, List<Integer>> entry : edges.entrySet()) {
      List<Integer> targets = entry.getValue();
      Set<Integer> unique = new HashSet<>(targets);
      assertEquals(unique.size(), targets.size(), "Duplicate center target detected for source " + entry.getKey());
    }
  }
}

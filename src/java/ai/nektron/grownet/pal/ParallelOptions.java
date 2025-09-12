package ai.nektron.grownet.pal;

public final class ParallelOptions {
  public Integer maxWorkers = null;
  public int tileSize = 4096;
  public String reductionMode = "ordered"; // "ordered" | "pairwise_tree"
  public String device = "cpu";            // "cpu" | "gpu" | "auto"
  public boolean vectorizationEnabled = true;
}


package ai.nektron.grownet.pal;

import java.util.List;

public final class PalDemo {
  public static void main(String[] args) {
    ParallelOptions opts = new ParallelOptions();
    opts.tileSize = 2048;
    IndexDomain domain = new IndexDomain(10_000);

    double sum = PAL.parallelMap(domain,
        (Integer i) -> {
          double v = i.doubleValue();
          return v * v;
        },
        (List<Double> locals) -> {
          double total = 0.0; for (double x : locals) total += x; return total;
        }, opts);

    System.out.println("[PAL Demo] sum of squares 0..9999 = " + (long)sum);
  }
}

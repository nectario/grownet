package ai.nektron.grownet.pal;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Consumer;
import java.util.function.Function;

public final class PAL {
  private static ParallelOptions GLOBAL = new ParallelOptions();

  private PAL() {}

  public static void configure(ParallelOptions options) {
    GLOBAL = (options == null ? new ParallelOptions() : options);
  }

  public static <T> void parallelFor(Domain<T> domain, Consumer<T> kernel, ParallelOptions opts) {
    Objects.requireNonNull(domain, "domain");
    Objects.requireNonNull(kernel, "kernel");
    // Sequential fallback: run in deterministic iteration order.
    for (T item : domain) {
      kernel.accept(item);
    }
  }

  public static <T, R> R parallelMap(Domain<T> domain,
                                     Function<T, R> kernel,
                                     Function<List<R>, R> reduceInOrder,
                                     ParallelOptions opts) {
    Objects.requireNonNull(domain, "domain");
    Objects.requireNonNull(kernel, "kernel");
    Objects.requireNonNull(reduceInOrder, "reduceInOrder");
    List<R> locals = new ArrayList<>();
    for (T item : domain) {
      locals.add(kernel.apply(item));
    }
    return reduceInOrder.apply(locals);
  }

  public static double counterRng(long seed,
                                  long step,
                                  int drawKind,
                                  int layerIndex,
                                  int unitIndex,
                                  int drawIndex) {
    long key = seed;
    key = mix64(key ^ step);
    key = mix64(key ^ drawKind);
    key = mix64(key ^ layerIndex);
    key = mix64(key ^ unitIndex);
    key = mix64(key ^ drawIndex);
    long mantissa = (key >>> 11) & ((1L << 53) - 1L);
    return mantissa / (double) (1L << 53);
  }

  private static long mix64(long x) {
    // SplitMix64 mixing
    long z = x + 0x9E3779B97F4A7C15L;
    z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
    z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
    z = z ^ (z >>> 31);
    return z;
  }
}


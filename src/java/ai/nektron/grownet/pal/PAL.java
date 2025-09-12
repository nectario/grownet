package ai.nektron.grownet.pal;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;
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

    // Enumerate domain deterministically
    final List<T> items = new ArrayList<>();
    domain.forEach(items::add);
    final int n = items.size();
    if (n == 0) return;

    final int tile = Math.max(1, (opts != null ? opts.tileSize : GLOBAL.tileSize));
    final Integer mw = (opts != null ? opts.maxWorkers : GLOBAL.maxWorkers);
    final int maxWorkers = Math.max(1, (mw != null ? mw : Runtime.getRuntime().availableProcessors()));
    final int tileCount = (n + tile - 1) / tile;

    final Semaphore permits = new Semaphore(maxWorkers, false);
    try (ExecutorService vexec = Executors.newVirtualThreadPerTaskExecutor()) {
      final List<Future<Void>> futures = new ArrayList<>(tileCount);
      for (int start = 0; start < n; start += tile) {
        final int s = start;
        final int e = Math.min(n, start + tile);
        futures.add(vexec.submit((Callable<Void>) () -> {
          try {
            permits.acquire();
            for (int i = s; i < e; i++) {
              kernel.accept(items.get(i));
            }
            return null;
          } finally {
            permits.release();
          }
        }));
      }
      // Barrier
      for (Future<Void> f : futures) {
        f.get();
      }
    } catch (InterruptedException ie) {
      Thread.currentThread().interrupt();
      throw new RuntimeException(ie);
    } catch (ExecutionException ee) {
      throw new RuntimeException(ee.getCause());
    }
  }

  public static <T, R> R parallelMap(Domain<T> domain,
                                     Function<T, R> kernel,
                                     Function<List<R>, R> reduceInOrder,
                                     ParallelOptions opts) {
    Objects.requireNonNull(domain, "domain");
    Objects.requireNonNull(kernel, "kernel");
    Objects.requireNonNull(reduceInOrder, "reduceInOrder");

    // Enumerate deterministically
    final List<T> items = new ArrayList<>();
    domain.forEach(items::add);
    final int n = items.size();
    if (n == 0) {
      return reduceInOrder.apply(List.of());
    }

    final int tile = Math.max(1, (opts != null ? opts.tileSize : GLOBAL.tileSize));
    final Integer mw = (opts != null ? opts.maxWorkers : GLOBAL.maxWorkers);
    final int maxWorkers = Math.max(1, (mw != null ? mw : Runtime.getRuntime().availableProcessors()));
    final int tileCount = (n + tile - 1) / tile;

    final Semaphore permits = new Semaphore(maxWorkers, false);
    @SuppressWarnings("unchecked")
    final List<R>[] partials = (List<R>[]) new List<?>[tileCount];

    try (ExecutorService vexec = Executors.newVirtualThreadPerTaskExecutor()) {
      final List<Future<Void>> futures = new ArrayList<>(tileCount);
      int tileIndex = 0;
      for (int start = 0; start < n; start += tile, tileIndex++) {
        final int s = start;
        final int e = Math.min(n, start + tile);
        final int idx = tileIndex;
        futures.add(vexec.submit((Callable<Void>) () -> {
          try {
            permits.acquire();
            final List<R> local = new ArrayList<>(e - s);
            for (int i = s; i < e; i++) {
              local.add(kernel.apply(items.get(i)));
            }
            partials[idx] = local;
            return null;
          } finally {
            permits.release();
          }
        }));
      }
      for (Future<Void> f : futures) { f.get(); }
    } catch (InterruptedException ie) {
      Thread.currentThread().interrupt();
      throw new RuntimeException(ie);
    } catch (ExecutionException ee) {
      throw new RuntimeException(ee.getCause());
    }

    // Deterministic reduction: flatten by tile index then in‑tile order
    final List<R> flat = new ArrayList<>(n);
    for (int t = 0; t < tileCount; t++) {
      final List<R> local = partials[t];
      if (local != null) flat.addAll(local);
    }
    return reduceInOrder.apply(flat);
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

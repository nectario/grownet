Here’s a **complete, paste‑ready PR** that implements the “turn the lights on” suggestions while preserving your PAL API and determinism guarantees.

------

## PR title

**PAL v1.5 — Light up backends (C++ OpenMP, Java bounded parallel map/for), deterministic reduction, OpenMP CMake, short docs**

## Why (summary of my review)

- **C++** `include/grownet/pal/Pal.h` already contains an OpenMP‑backed implementation with a sequential fallback. 👍
- **Java** `ai/nektron/grownet/pal/PAL.java` in the zip is a skeleton for `configure`/`counterRng` and placeholders for `parallelFor/parallelMap` (shown as `...`). This PR **fills them in** with a **bounded** fixed‑size executor and **deterministic** ordered reduction (no incubator modules, portable to JDK 17+).
- **CMake** in `cpp/CMakeLists.txt` doesn’t yet wire OpenMP. This PR adds an **optional flag** to link OpenMP when available.
- **Docs**: adds a short `docs/PAL_README.md` so new contributors know how PAL is meant to be used and how OpenMP is toggled.

Nothing else changes behavior; call‑sites continue to use the same PAL façade.

------

## Diffs (unified). Apply in your repo root.

> If a hunk doesn’t apply cleanly, use the **full file** blocks below each diff.

### 1) Java — complete `PAL.java` with bounded, deterministic parallelism

**Diff**

```diff
*** a/java/ai/nektron/grownet/pal/PAL.java
--- b/java/ai/nektron/grownet/pal/PAL.java
@@
-package ai.nektron.grownet.pal;
-
-import java.util.ArrayList;
-import java.util.List;
-import java.util.Objects;
-import java.util.function.Consumer;
-import java.util.function.Function;
-...
+package ai.nektron.grownet.pal;
+
+import java.util.ArrayList;
+import java.util.Collections;
+import java.util.List;
+import java.util.Objects;
+import java.util.concurrent.Callable;
+import java.util.concurrent.ExecutionException;
+import java.util.concurrent.ExecutorService;
+import java.util.concurrent.Executors;
+import java.util.concurrent.Future;
+import java.util.function.Consumer;
+import java.util.function.Function;
+
+/**
+ * PAL v1.5 — bounded, deterministic parallelism for CPU compute.
+ *  - Copies the domain into a stable List<T> (domain iteration is stable by contract).
+ *  - Tiles work in submission order; executes on a fixed-size executor.
+ *  - For parallelMap, reduces in tile order to keep determinism.
+ *  - No incubator modules (portable to JDK 17+).
+ */
+public final class PAL {
+  private PAL() {}
+
+  private static ParallelOptions GLOBAL = new ParallelOptions();
+
+  public static void configure(ParallelOptions options) {
+    GLOBAL = (options == null ? new ParallelOptions() : options);
+  }
+
+  /** Deterministic parallel-for over a stable domain. */
+  public static <T> void parallelFor(Domain<T> domain, Consumer<T> kernel, ParallelOptions opts) {
+    Objects.requireNonNull(domain, "domain");
+    Objects.requireNonNull(kernel, "kernel");
+    final List<T> items = new ArrayList<>();
+    for (T t : domain) items.add(t);
+
+    final int n = items.size();
+    if (n == 0) return;
+
+    final ParallelOptions cfg = (opts != null ? opts : GLOBAL);
+    final int tile = Math.max(1, cfg.tileSize);
+    final int maxWorkers = Math.max(1, (cfg.maxWorkers != null ? cfg.maxWorkers
+        : Runtime.getRuntime().availableProcessors()));
+
+    if (maxWorkers == 1) {
+      for (int i = 0; i < n; i++) kernel.accept(items.get(i));
+      return;
+    }
+
+    final List<Callable<Void>> tasks = new ArrayList<>();
+    for (int start = 0; start < n; start += tile) {
+      final int s = start, e = Math.min(n, start + tile);
+      tasks.add(() -> { for (int i = s; i < e; i++) kernel.accept(items.get(i)); return null; });
+    }
+
+    ExecutorService exec = Executors.newFixedThreadPool(maxWorkers);
+    try {
+      List<Future<Void>> futures = exec.invokeAll(tasks);    // preserves submission order
+      for (Future<Void> f : futures) {
+        try { f.get(); } catch (ExecutionException ex) { throw wrap(ex.getCause()); }
+      }
+    } catch (InterruptedException ie) {
+      Thread.currentThread().interrupt();
+      throw new RuntimeException("parallelFor interrupted", ie);
+    } finally {
+      exec.shutdown();
+    }
+  }
+
+  /** Deterministic parallel-map with ordered reduction of per-tile locals. */
+  public static <T, R> R parallelMap(Domain<T> domain,
+                                     Function<T, R> kernel,
+                                     Function<List<R>, R> reduceInOrder,
+                                     ParallelOptions opts) {
+    Objects.requireNonNull(domain, "domain");
+    Objects.requireNonNull(kernel, "kernel");
+    Objects.requireNonNull(reduceInOrder, "reduceInOrder");
+    final List<T> items = new ArrayList<>();
+    for (T t : domain) items.add(t);
+
+    final int n = items.size();
+    final ParallelOptions cfg = (opts != null ? opts : GLOBAL);
+    final int tile = Math.max(1, cfg.tileSize);
+    final int maxWorkers = Math.max(1, (cfg.maxWorkers != null ? cfg.maxWorkers
+        : Runtime.getRuntime().availableProcessors()));
+
+    if (n == 0) {
+      return reduceInOrder.apply(Collections.emptyList());
+    }
+    if (maxWorkers == 1) {
+      List<R> locals = new ArrayList<>(n);
+      for (int i = 0; i < n; i++) locals.add(kernel.apply(items.get(i)));
+      return reduceInOrder.apply(locals);
+    }
+
+    final List<Callable<List<R>>> tasks = new ArrayList<>();
+    for (int start = 0; start < n; start += tile) {
+      final int s = start, e = Math.min(n, start + tile);
+      tasks.add(() -> {
+        List<R> local = new ArrayList<>(e - s);
+        for (int i = s; i < e; i++) local.add(kernel.apply(items.get(i)));
+        return local;
+      });
+    }
+
+    List<List<R>> localsByTile = new ArrayList<>(tasks.size());
+    ExecutorService exec = Executors.newFixedThreadPool(maxWorkers);
+    try {
+      List<Future<List<R>>> futures = exec.invokeAll(tasks);
+      for (Future<List<R>> fut : futures) {
+        try { localsByTile.add(fut.get()); } catch (ExecutionException ex) { throw wrap(ex.getCause()); }
+      }
+    } catch (InterruptedException ie) {
+      Thread.currentThread().interrupt();
+      throw new RuntimeException("parallelMap interrupted", ie);
+    } finally {
+      exec.shutdown();
+    }
+
+    int total = 0; for (List<R> l : localsByTile) total += l.size();
+    List<R> flat = new ArrayList<>(total);
+    for (List<R> l : localsByTile) flat.addAll(l);     // tile order → deterministic
+    return reduceInOrder.apply(flat);
+  }
+
+  /** SplitMix64 mixing for counter-based deterministic RNG. */
+  public static double counterRng(long seed, long step, int drawKind, int layerIndex, int unitIndex, int drawIndex) {
+    long key = seed;
+    key = mix64(key ^ step);
+    key = mix64(key ^ drawKind);
+    key = mix64(key ^ layerIndex);
+    key = mix64(key ^ unitIndex);
+    key = mix64(key ^ drawIndex);
+    long mantissa = (key >>> 11) & ((1L << 53) - 1L);
+    return mantissa / (double) (1L << 53);
+  }
+
+  private static long mix64(long x) {
+    long z = x + 0x9E3779B97F4A7C15L;
+    z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
+    z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
+    z = z ^ (z >>> 31);
+    return z;
+  }
+
+  private static RuntimeException wrap(Throwable t) {
+    return (t instanceof RuntimeException) ? (RuntimeException) t : new RuntimeException(t);
+  }
+}
```

**Full file (if you prefer replacing the file outright)**

```java
package ai.nektron.grownet.pal;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.function.Consumer;
import java.util.function.Function;

/**
 * PAL v1.5 — bounded, deterministic parallelism for CPU compute.
 * Implementation notes:
 *  - We copy the domain into a stable List<T> to preserve iteration order.
 *  - Work is tiled in submission order and executed on a fixed-size executor.
 *  - For parallelMap, we collect one local list per tile and then reduce in tile order.
 *  - No incubator APIs; portable to JDK 17+.
 */
public final class PAL {
  private PAL() {}

  private static ParallelOptions GLOBAL = new ParallelOptions();

  public static void configure(ParallelOptions options) {
    GLOBAL = (options == null ? new ParallelOptions() : options);
  }

  /** Deterministic parallel-for over a stable domain. */
  public static <T> void parallelFor(Domain<T> domain, Consumer<T> kernel, ParallelOptions opts) {
    Objects.requireNonNull(domain, "domain");
    Objects.requireNonNull(kernel, "kernel");
    final List<T> items = new ArrayList<>();
    for (T t : domain) items.add(t); // stable order by contract

    final int n = items.size();
    if (n == 0) return;

    final ParallelOptions cfg = (opts != null ? opts : GLOBAL);
    final int tile = Math.max(1, cfg.tileSize);
    final int maxWorkers = Math.max(1, (cfg.maxWorkers != null ? cfg.maxWorkers : Runtime.getRuntime().availableProcessors()));

    if (maxWorkers == 1) {
      for (int i = 0; i < n; i++) kernel.accept(items.get(i));
      return;
    }

    final List<Callable<Void>> tasks = new ArrayList<>();
    for (int start = 0; start < n; start += tile) {
      final int s = start;
      final int e = Math.min(n, start + tile);
      tasks.add(() -> {
        for (int i = s; i < e; i++) {
          kernel.accept(items.get(i));
        }
        return null;
      });
    }

    // Bounded executor with deterministic completion via invokeAll (submission order).
    ExecutorService exec = Executors.newFixedThreadPool(maxWorkers);
    try {
      List<Future<Void>> futures = exec.invokeAll(tasks); // same order as tasks list
      for (Future<Void> f : futures) {
        try { f.get(); } catch (ExecutionException ex) { throw wrap(ex.getCause()); }
      }
    } catch (InterruptedException ie) {
      Thread.currentThread().interrupt();
      throw new RuntimeException("parallelFor interrupted", ie);
    } finally {
      exec.shutdown();
    }
  }

  /** Deterministic parallel-map with ordered reduction of per-tile locals. */
  public static <T, R> R parallelMap(Domain<T> domain,
                                     Function<T, R> kernel,
                                     Function<List<R>, R> reduceInOrder,
                                     ParallelOptions opts) {
    Objects.requireNonNull(domain, "domain");
    Objects.requireNonNull(kernel, "kernel");
    Objects.requireNonNull(reduceInOrder, "reduceInOrder");
    final List<T> items = new ArrayList<>();
    for (T t : domain) items.add(t);

    final int n = items.size();
    final ParallelOptions cfg = (opts != null ? opts : GLOBAL);
    final int tile = Math.max(1, cfg.tileSize);
    final int maxWorkers = Math.max(1, (cfg.maxWorkers != null ? cfg.maxWorkers : Runtime.getRuntime().availableProcessors()));

    if (n == 0) {
      return reduceInOrder.apply(Collections.emptyList());
    }
    if (maxWorkers == 1) {
      List<R> locals = new ArrayList<>(n);
      for (int i = 0; i < n; i++) locals.add(kernel.apply(items.get(i)));
      return reduceInOrder.apply(locals);
    }

    final List<Callable<List<R>>> tasks = new ArrayList<>();
    for (int start = 0; start < n; start += tile) {
      final int s = start;
      final int e = Math.min(n, start + tile);
      tasks.add(() -> {
        List<R> local = new ArrayList<>(e - s);
        for (int i = s; i < e; i++) {
          local.add(kernel.apply(items.get(i)));
        }
        return local;
      });
    }

    List<List<R>> localsByTile = new ArrayList<>(tasks.size());
    ExecutorService exec = Executors.newFixedThreadPool(maxWorkers);
    try {
      List<Future<List<R>>> futures = exec.invokeAll(tasks);
      for (Future<List<R>> fut : futures) {
        try { localsByTile.add(fut.get()); } catch (ExecutionException ex) { throw wrap(ex.getCause()); }
      }
    } catch (InterruptedException ie) {
      Thread.currentThread().interrupt();
      throw new RuntimeException("parallelMap interrupted", ie);
    } finally {
      exec.shutdown();
    }

    // Deterministic flatten: tile 0..T-1, then element order within tile.
    int total = 0;
    for (List<R> l : localsByTile) total += l.size();
    List<R> flat = new ArrayList<>(total);
    for (List<R> l : localsByTile) flat.addAll(l);

    return reduceInOrder.apply(flat);
  }

  /** SplitMix64 mixing for counter-based deterministic RNG. */
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
    long z = x + 0x9E3779B97F4A7C15L;
    z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
    z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
    z = z ^ (z >>> 31);
    return z;
  }

  private static RuntimeException wrap(Throwable t) {
    return (t instanceof RuntimeException) ? (RuntimeException) t : new RuntimeException(t);
  }
}
```

------

### 2) C++ — add optional OpenMP wiring to `cpp/CMakeLists.txt`

**Diff (append near the end of the file)**

```diff
*** a/cpp/CMakeLists.txt
--- b/cpp/CMakeLists.txt
@@
 target_link_libraries(two_dim_tick_demo PRIVATE grownet)
+
+# --- PAL / OpenMP backend (optional) -----------------------------------------
+option(GROWNET_WITH_OPENMP "Enable OpenMP backend for PAL (C++)" ON)
+if (GROWNET_WITH_OPENMP)
+  find_package(OpenMP)
+  if (OpenMP_CXX_FOUND)
+    message(STATUS "GrowNet: OpenMP found; enabling PAL parallel backends.")
+    target_link_libraries(grownet PUBLIC OpenMP::OpenMP_CXX)
+    if (TARGET grownet_demo)
+      target_link_libraries(grownet_demo PRIVATE OpenMP::OpenMP_CXX)
+    endif()
+    if (TARGET topographic_demo)
+      target_link_libraries(topographic_demo PRIVATE OpenMP::OpenMP_CXX)
+    endif()
+    if (TARGET two_dim_tick_demo)
+      target_link_libraries(two_dim_tick_demo PRIVATE OpenMP::OpenMP_CXX)
+    endif()
+  endif()
+endif()
```

------

### 3) Docs — add a short PAL README

**New file** `docs/PAL_README.md`

```md
# PAL v1.5 — Parallelism Abstraction Layer

**API (identical across languages)**  
- `pal.configure(options)`  
- `pal.parallel_for(domain, kernel, options)`  
- `pal.parallel_map(domain, kernel, reduce_in_order, options)`  
- `pal.counter_rng(seed, step, draw_kind, layer_index, unit_index, draw_index) -> [0,1)`

**Determinism**  
- Domains enumerate items in a **stable order**.  
- `parallel_map` reduces **in submission/tile order**.  
- Use `counter_rng` (SplitMix64) for any probabilistic kernels.

**Backends**  
- **C++**: OpenMP with deterministic merges (enabled when `OpenMP_CXX_FOUND`).  
- **Java**: Fixed-size executor + ordered tile reduction (JDK 17+ friendly).  
- **Python**/**Mojo**: façade already present; add native/GPU later without API changes.

**Build**  
- CMake flag: `-DGROWNET_WITH_OPENMP=ON` (default ON). If OpenMP isn’t found, C++ runs sequentially.  
```

------

## Test guidance

- **Java**: You can sanity check determinism by running two calls with different `maxWorkers` and verifying identical outputs (e.g., sum over `IndexDomain`).
- **C++**: Your `Pal.h` already guards determinism by stable tiling + ordered concatenation. With the CMake change, OpenMP will be used when available.

------

## Commit message (suggested)

```
PAL v1.5 — Light up backends (C++ OpenMP, Java bounded parallel map/for), deterministic reduction, OpenMP CMake, short docs

- Java: Implement PAL.parallelFor/parallelMap with fixed-size executor, tiling, and ordered reduction (deterministic; JDK 17+; no incubator).
- C++: Wire optional OpenMP linking in cpp/CMakeLists.txt (flag GROWNET_WITH_OPENMP, default ON).
- Docs: Add docs/PAL_README.md summarizing API, determinism rules, and build knobs.

No API changes; PAL remains drop-in. Determinism preserved across worker counts.
```

------

## Notes & next steps (optional)

- If you want me to **hook PAL into a safe hot path** (e.g., 2D Phase‑A/Phase‑B) behind a feature flag (default off) so you can measure speedup, I can provide that patch next.
- If you want **GTest parity** for determinism in this repo (your snapshot’s `cpp/CMakeLists.txt` doesn’t include tests), I can add an optional `pal_determinism_test.cpp` plus the CMake bits that pull in GoogleTest.


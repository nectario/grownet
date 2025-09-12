Below is a **drop‑in PR** that switches the Java PAL to **Virtual Threads** (Loom) while **preserving determinism** and honoring `ParallelOptions.maxWorkers` and `tileSize`.

It does **not** change the public API shape (so it stays aligned with Python/C++/Mojo). The only change is inside the PAL implementation.

------

## PR title

**Java PAL: Virtual Threads backend with deterministic ordered reduction (bounded by `maxWorkers`)**

## Rationale (1‑minute read)

- **Virtual Threads** orchestrate tile tasks; each task runs in a vthread.
- **Concurrency bound**: a `Semaphore(maxWorkers)` caps how many vthreads do CPU work at once (no oversubscription).
- **Determinism**:
  - We enumerate the `Domain` into a **stable `items` list**.
  - We build **contiguous tiles** in that order.
  - `parallel_map` writes each tile’s results into a **pre‑indexed slot**, then **flattens by tile index**; `parallel_for` just executes tiles.
  - Final `reduceInOrder` sees values in **canonical order**, independent of scheduling.

> JDK 21+ is assumed (no incubator modules required). If you’re on JDK ≤20, keep the old sequential path.

------

## Patch: `src/java/ai/nektron/grownet/pal/PAL.java`

> This replaces only the method bodies—**public API unchanged**.

```diff
*** a/src/java/ai/nektron/grownet/pal/PAL.java
--- b/src/java/ai/nektron/grownet/pal/PAL.java
@@
 package ai.nektron.grownet.pal;

 import java.util.ArrayList;
 import java.util.List;
 import java.util.Objects;
+import java.util.concurrent.Callable;
+import java.util.concurrent.ExecutionException;
+import java.util.concurrent.ExecutorService;
+import java.util.concurrent.Executors;
+import java.util.concurrent.Future;
+import java.util.concurrent.Semaphore;
 import java.util.function.Consumer;
 import java.util.function.Function;

 public final class PAL {
   private static ParallelOptions GLOBAL = new ParallelOptions();
@@
-  public static <T> void parallelFor(Domain<T> domain, Consumer<T> kernel, ParallelOptions opts) {
-    Objects.requireNonNull(domain, "domain");
-    Objects.requireNonNull(kernel, "kernel");
-    // Sequential fallback: run in deterministic iteration order.
-    for (T item : domain) {
-      kernel.accept(item);
-    }
-  }
+  public static <T> void parallelFor(Domain<T> domain, Consumer<T> kernel, ParallelOptions opts) {
+    Objects.requireNonNull(domain, "domain");
+    Objects.requireNonNull(kernel, "kernel");
+    final List<T> items = new ArrayList<>();
+    domain.forEach(items::add); // stable order from Domain
+    final int n = items.size();
+    if (n == 0) return;
+    final int tile = Math.max(1, (opts != null ? opts.tileSize : GLOBAL.tileSize));
+    final int maxWorkers = Math.max(1, (opts != null && opts.maxWorkers != null) ? opts.maxWorkers : Runtime.getRuntime().availableProcessors());
+    final int tileCount = (n + tile - 1) / tile;
+    final Semaphore permits = new Semaphore(maxWorkers, false);
+    try (ExecutorService vexec = Executors.newVirtualThreadPerTaskExecutor()) {
+      final List<Future<Void>> futures = new ArrayList<>(tileCount);
+      for (int start = 0; start < n; start += tile) {
+        final int s = start;
+        final int e = Math.min(n, start + tile);
+        futures.add(vexec.submit((Callable<Void>) () -> {
+          try {
+            permits.acquire();
+            for (int i = s; i < e; i++) {
+              kernel.accept(items.get(i));
+            }
+            return null;
+          } finally {
+            permits.release();
+          }
+        }));
+      }
+      // Barrier
+      for (Future<Void> f : futures) {
+        f.get();
+      }
+    } catch (InterruptedException ie) {
+      Thread.currentThread().interrupt();
+      throw new RuntimeException(ie);
+    } catch (ExecutionException ee) {
+      throw new RuntimeException(ee.getCause());
+    }
+  }
@@
-  public static <T, R> R parallelMap(Domain<T> domain,
-                                     Function<T, R> kernel,
-                                     Function<List<R>, R> reduceInOrder,
-                                     ParallelOptions opts) {
-    Objects.requireNonNull(domain, "domain");
-    Objects.requireNonNull(kernel, "kernel");
-    Objects.requireNonNull(reduceInOrder, "reduceInOrder");
-    List<R> locals = new ArrayList<>();
-    for (T item : domain) {
-      locals.add(kernel.apply(item));
-    }
-    return reduceInOrder.apply(locals);
-  }
+  public static <T, R> R parallelMap(Domain<T> domain,
+                                     Function<T, R> kernel,
+                                     Function<List<R>, R> reduceInOrder,
+                                     ParallelOptions opts) {
+    Objects.requireNonNull(domain, "domain");
+    Objects.requireNonNull(kernel, "kernel");
+    Objects.requireNonNull(reduceInOrder, "reduceInOrder");
+    final List<T> items = new ArrayList<>();
+    domain.forEach(items::add); // stable order
+    final int n = items.size();
+    if (n == 0) {
+      return reduceInOrder.apply(List.of());
+    }
+    final int tile = Math.max(1, (opts != null ? opts.tileSize : GLOBAL.tileSize));
+    final int maxWorkers = Math.max(1, (opts != null && opts.maxWorkers != null) ? opts.maxWorkers : Runtime.getRuntime().availableProcessors());
+    final int tileCount = (n + tile - 1) / tile;
+    final Semaphore permits = new Semaphore(maxWorkers, false);
+    @SuppressWarnings("unchecked")
+    final List<R>[] partials = (List<R>[]) new List<?>[tileCount];
+    try (ExecutorService vexec = Executors.newVirtualThreadPerTaskExecutor()) {
+      final List<Future<Void>> futures = new ArrayList<>(tileCount);
+      int tileIndex = 0;
+      for (int start = 0; start < n; start += tile, tileIndex++) {
+        final int s = start;
+        final int e = Math.min(n, start + tile);
+        final int idx = tileIndex; // capture tile index
+        futures.add(vexec.submit((Callable<Void>) () -> {
+          try {
+            permits.acquire();
+            final List<R> local = new ArrayList<>(e - s);
+            for (int i = s; i < e; i++) {
+              local.add(kernel.apply(items.get(i)));
+            }
+            partials[idx] = local; // publish to deterministic slot
+            return null;
+          } finally {
+            permits.release();
+          }
+        }));
+      }
+      for (Future<Void> f : futures) { f.get(); } // barrier
+    } catch (InterruptedException ie) {
+      Thread.currentThread().interrupt();
+      throw new RuntimeException(ie);
+    } catch (ExecutionException ee) {
+      throw new RuntimeException(ee.getCause());
+    }
+    // Deterministic reduction: flatten by tile index, then in‑tile order
+    final List<R> flat = new ArrayList<>(n);
+    for (int t = 0; t < tileCount; t++) {
+      final List<R> local = partials[t];
+      if (local != null) flat.addAll(local);
+    }
+    return reduceInOrder.apply(flat);
+  }
```

> `counterRng(...)` and `mix64(...)` remain as you had them—unchanged.



#### Finally: Please add a small JUnit test (`PalDeterminismTest`) mirroring the C++ determinism test. 

## How to build & run

- **JDK**: 21+ (Virtual Threads are final in 21).
- **No extra flags** required (we don’t use incubator Structured Concurrency here).
- **Behavior**:
  - With `maxWorkers = null`, we use `availableProcessors()`.
  - Determinism is preserved for both `parallelFor` and `parallelMap`.

------

## Quick smoke test (optional)

Add this ad‑hoc kernel somewhere to confirm vthreads are being used:

```java
PAL.parallelFor(new IndexDomain(10_000), (Integer i) -> {
  if (i == 0) {
    System.out.println("kernel runs in virtual thread? " + Thread.currentThread().isVirtual());
  }
}, null);
```

You should see `true`.

------

## Why this is safe

- **Public API unchanged** (no divergence with other languages).
- **Deterministic**: tile → slot → ordered flatten → `reduceInOrder`.
- **Bounded parallelism**: avoids carrier oversubscription during CPU‑bound loops.
- **No leading underscores** introduced.


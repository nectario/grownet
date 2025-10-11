// Bench (Java) — InputLayer2D -> mixed Layer -> OutputLayer2D
// Build: compile alongside the existing sources; run with classpath to build output
// Usage: java ai.nektron.grownet.bench.BenchJava --scenario image_64x64 --json

package ai.nektron.grownet.bench;

import ai.nektron.grownet.Region;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public final class BenchJava {
    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> m = new HashMap<>();
        for (int i = 0; i < args.length; ++i) {
            if ("--scenario".equals(args[i]) && i + 1 < args.length) m.put("scenario", args[++i]);
            else if ("--json".equals(args[i])) m.put("json", "1");
        }
        return m;
    }

    public static void main(String[] args) {
        Map<String, String> a = parseArgs(args);
        String scenario = a.getOrDefault("scenario", "image_64x64");

        // Defaults
        int frames = 100, h = 64, w = 64;
        int excit = 512, inhib = 64, mod = 16;
        String port = "pixels";

        Region region = new Region("bench_java");
        int mid = region.addLayer(excit, inhib, mod);
        int out = region.addOutputLayer2D(h, w, 0.2);
        region.bindInput2D(port, h, w, 1.0, 0.01, java.util.List.of(mid));
        region.connectLayers(mid, out, 0.02, false);

        double[][] frame = new double[h][w];
        Random rng = new Random(1234);
        java.util.function.Supplier<double[][]> makeFrame = () -> {
            for (int r = 0; r < h; ++r) {
                for (int c = 0; c < w; ++c) frame[r][c] = rng.nextDouble();
            }
            return frame;
        };

        // Warmup
        region.tickImage(port, makeFrame.get());

        long t0 = System.nanoTime();
        long delivered = 0;
        for (int i = 0; i < frames; ++i) {
            var m = region.tickImage(port, makeFrame.get());
            delivered += m.getDeliveredEvents();
        }
        long t1 = System.nanoTime();
        double ms = (t1 - t0) / 1_000_000.0;

        String json = String.format("{\"impl\":\"java\",\"scenario\":\"%s\",\"runs\":1,"
                + "\"metrics\":{\"e2e_wall_ms\":%.3f,\"ticks\":%d,\"per_tick_us_avg\":%.3f,\"delivered_events\":%d}}",
                scenario, ms, frames, (ms * 1000.0 / frames), delivered);
        System.out.println(json);
    }
}


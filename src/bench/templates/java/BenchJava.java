// Suggested location: src/java/ai/nektron/grownet/bench/BenchJava.java
// Build: include in your existing build. Requires your Region / Layer / InputLayer2D / OutputLayer2D.
// Usage: java ai.nektron.grownet.bench.BenchJava --scenario image_64x64 --json

package ai.nektron.grownet.bench;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.Layer;
import ai.nektron.grownet.InputLayer2D;
import ai.nektron.grownet.OutputLayer2D;

import java.util.Random;
import java.util.HashMap;
import java.util.Map;

public final class BenchJava {
    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> m = new HashMap<>();
        for (int i=0; i<args.length; ++i) {
            if ("--scenario".equals(args[i]) && i+1 < args.length) m.put("scenario", args[++i]);
            else if ("--json".equals(args[i])) m.put("json", "1");
        }
        return m;
    }

    public static void main(String[] args) {
        Map<String, String> a = parseArgs(args);
        String scenario = a.getOrDefault("scenario", "image_64x64");

        int frames = 100, h = 64, w = 64;
        int excit = 512, inhib = 64, mod = 16;

        Region region = new Region("bench_java");
        Layer in  = new InputLayer2D(h, w, 1.0, 0.01);
        Layer mid = new Layer(excit, inhib, mod);
        Layer out = new OutputLayer2D(h, w, 0.2);

        region.getLayers().add(in);
        region.getLayers().add(mid);
        region.getLayers().add(out);

        mid.wireRandomFeedforward(0.02);
        out.wireRandomFeedforward(0.02);

        double[][] frame = new double[h][w];
        Random rng = new Random(1234);

        long t0 = System.nanoTime();
        for (int f=0; f<frames; ++f) {
            for (int y=0; y<h; ++y) for (int x=0; x<w; ++x) frame[y][x] = rng.nextDouble();
            region.tickImage("pixels", frame);
        }
        long t1 = System.nanoTime();
        double ms = (t1 - t0) / 1_000_000.0;

        String json = String.format("{\"impl\":\"java\",\"scenario\":\"%s\",\"runs\":1," +
                "\"metrics\":{\"e2e_wall_ms\":%.3f,\"ticks\":%d,\"per_tick_us_avg\":%.3f}}",
                scenario, ms, frames, (ms*1000.0/frames));
        System.out.println(json);
    }
}

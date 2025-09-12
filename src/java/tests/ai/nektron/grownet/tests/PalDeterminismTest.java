package ai.nektron.grownet.tests;

import ai.nektron.grownet.pal.IndexDomain;
import ai.nektron.grownet.pal.PAL;
import ai.nektron.grownet.pal.ParallelOptions;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class PalDeterminismTest {

    @Test
    public void orderedReductionIdenticalAcrossWorkers() {
        final int N = 10_000;
        IndexDomain domain = new IndexDomain(N);

        var kernel = (Integer i) -> PAL.counterRng(/*seed*/1234L, /*step*/0L,
                /*drawKind*/1, /*layerIndex*/0, /*unitIndex*/i, /*drawIndex*/0);

        var reduceInOrder = (List<Double> locals) -> {
            double s = 0.0;
            for (double x : locals) s += x;
            return s;
        };

        ParallelOptions one = new ParallelOptions();
        one.maxWorkers = 1; // single worker
        one.tileSize = 512;

        ParallelOptions many = new ParallelOptions();
        many.maxWorkers = Math.max(2, Runtime.getRuntime().availableProcessors());
        many.tileSize = 512;

        double a = PAL.parallelMap(domain, kernel, reduceInOrder, one);
        double b = PAL.parallelMap(domain, kernel, reduceInOrder, many);

        assertEquals(a, b, 0.0, "PAL.parallelMap must be deterministic across worker counts");
    }
}


// src/cpp/tests/WindowedWiringSmoke.cpp
// Compile this only in a local check; keep it out of production builds.
#ifdef GROWNET_WINDOWED_WIRING_SMOKE

#include <iostream>
#include <cassert>
#include "Region.h"

using grownet::Region;

static void run_case(int height, int width,
                     int kernelHeight, int kernelWidth,
                     int strideHeight, int strideWidth,
                     const std::string& padding,
                     int expectedUniqueSources) {
    Region testRegion("win-smoke");

    // NOTE: adjust the method names below if your Region API differs.
    const int inputLayer  = testRegion.addInputLayer2D(height, width, /*gain=*/1.0, /*epsilonFire=*/0.01);
    const int outputLayer = testRegion.addOutputLayer2D(height, width, /*smoothing=*/0.0);

    int wireCount = testRegion.connectLayersWindowed(inputLayer, outputLayer, kernelHeight, kernelWidth, strideHeight, strideWidth, padding, /*feedback=*/false);

    if (wireCount != expectedUniqueSources) {
        std::cerr << "[FAIL] height="<<height<<" width="<<width
                  << " kernelH="<<kernelHeight<<" kernelW="<<kernelWidth
                  << " strideH="<<strideHeight<<" strideW="<<strideWidth
                  << " padding="<<padding
                  << " got wires="<<wireCount
                  << " expected="<<expectedUniqueSources << "\n";
        std::exit(1);
    }
    std::cout << "[OK]  padding="<<padding<<" "
              << height<<"x"<<width<<" kernel="<<kernelHeight<<"x"<<kernelWidth
              << " stride="<<strideHeight<<"x"<<strideWidth
              << " \u2192 unique="<<wireCount << "\n";
}

int main() {
    // 1) 4×4, VALID, kernel 4×4 covers whole grid once → 16 uniques
    run_case(/*height*/4, /*width*/4, /*kernelHeight*/4, /*kernelWidth*/4, /*strideHeight*/1, /*strideWidth*/1, "valid", /*expectedUniqueSources*/16);

    // 2) 4×4, VALID, kernel 2×2, stride 2 tiles perfectly → 16 uniques
    run_case(4, 4, 2, 2, 2, 2, "valid", 16);

    // 3) 5×5, VALID, kernel 3×3, stride 3 → only origin (0,0) fits → 9 uniques
    run_case(5, 5, 3, 3, 3, 3, "valid", 9);

    // 4) 5×5, SAME, kernel 3×3, stride 3 → four windows (-1,-1),( -1,2),(2,-1),(2,2) → covers all → 25 uniques
    run_case(5, 5, 3, 3, 3, 3, "same", 25);

    // 5) 4×4, SAME, kernel 2×2, stride 2 → SAME == VALID for even 2×2 with our center rule → 16
    run_case(4, 4, 2, 2, 2, 2, "same", 16);

    std::cout << "All windowed\u2011wiring smoke tests passed.\n";
    return 0;
}

#endif // GROWNET_WINDOWED_WIRING_SMOKE


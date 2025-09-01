// src/cpp/tests/WindowedWiringSmoke.cpp
// Compile this only in a local check; keep it out of production builds.
#ifdef GROWNET_WINDOWED_WIRING_SMOKE

#include <iostream>
#include <cassert>
#include "Region.h"

using grownet::Region;

static void run_case(int H, int W,
                     int kh, int kw,
                     int sh, int sw,
                     const std::string& pad,
                     int expected_unique_sources) {
    Region r("win-smoke");

    // NOTE: adjust the method names below if your Region API differs.
    const int in  = r.addInputLayer2D(H, W, /*gain=*/1.0, /*epsilonFire=*/0.01);
    const int out = r.addOutputLayer2D(H, W, /*smoothing=*/0.0);

    int wires = r.connectLayersWindowed(in, out, kh, kw, sh, sw, pad, /*feedback=*/false);

    if (wires != expected_unique_sources) {
        std::cerr << "[FAIL] H="<<H<<" W="<<W
                  << " kh="<<kh<<" kw="<<kw
                  << " sh="<<sh<<" sw="<<sw
                  << " pad="<<pad
                  << " got wires="<<wires
                  << " expected="<<expected_unique_sources << "\n";
        std::exit(1);
    }
    std::cout << "[OK]  pad="<<pad<<" "
              << H<<"x"<<W<<" kernel="<<kh<<"x"<<kw
              << " stride="<<sh<<"x"<<sw
              << " \u2192 unique="<<wires << "\n";
}

int main() {
    // 1) 4×4, VALID, kernel 4×4 covers whole grid once → 16 uniques
    run_case(/*H*/4, /*W*/4, /*kh*/4, /*kw*/4, /*sh*/1, /*sw*/1, "valid", /*expect*/16);

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


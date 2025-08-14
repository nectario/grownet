#include <iostream>
#include <random>
#include <vector>
#include "Region.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

using namespace grownet;

int main() {
    const int h = 28, w = 28;
    Region region("image_io");

    // Example: wire a tiny IO pipeline
    // (Layer creation helpers omitted for brevity in this demo main)

    std::mt19937 rng(42);
    std::uniform_real_distribution<double> uni(0.0, 1.0);

    for (int step = 0; step < 20; ++step) {
        std::vector<std::vector<double>> frame(h, std::vector<double>(w, 0.0));
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                frame[y][x] = (uni(rng) > 0.95) ? 1.0 : 0.0;
            }
        }

        RegionMetrics m {}; // placeholder; depends on your Region wiring

        if ((step + 1) % 5 == 0) {
            double sum = 0.0;
            int nonZero = 0;
            for (int y = 0; y < h; ++y) {
                for (int x = 0; x < w; ++x) {
                    sum += frame[y][x];
                    if (frame[y][x] > 0.05) ++nonZero;
                }
            }
            double mean = sum / (h * w);
            std::cout << "[" << (step + 1) << "] delivered=" << m.deliveredEvents
                      << " out_mean=" << mean << " out_nonzero=" << nonZero << "\n";
        }
    }
    return 0;
}
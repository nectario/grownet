#include <iostream>
#include <vector>
#include <random>
#include <memory>
#include "Region.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

int main() {
    using namespace grownet;
    const int h = 28, w = 28;
    Region region("image_io");
    int lIn     = region.addInputLayer2D(h, w, 1.0, 0.01);
    int lHidden = region.addLayer(64, 8, 4);
    int lOut    = region.addOutputLayer2D(h, w, 0.20);

    region.bindInput("pixels", { lIn });
    region.connectLayers(lIn, lHidden, 0.05, false);
    region.connectLayers(lHidden, lOut, 0.12, false);

    std::mt19937 rng(42);
    std::uniform_real_distribution<double> uni(0.0, 1.0);

    for (int step = 0; step < 20; ++step) {
        std::vector<std::vector<double>> frame(h, std::vector<double>(w, 0.0));
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                frame[y][x] = (uni(rng) > 0.95) ? 1.0 : 0.0;
            }
        }

        auto m = region.tickImage("pixels", frame);

        if ((step + 1) % 5 == 0) {
            auto outLayer = std::dynamic_pointer_cast<OutputLayer2D>(region.getLayers()[lOut]);
            const auto& img = outLayer->getFrame();

            double sum = 0.0;
            int nonZero = 0;
            for (int y = 0; y < h; ++y) {
                for (int x = 0; x < w; ++x) {
                    sum += img[y][x];
                    if (img[y][x] > 0.05) nonZero++;
                }
            }
            double mean = sum / (h * w);
            std::cout << "[" << (step + 1) << "] delivered=" << m.getDeliveredEvents()
                      << " out_mean=" << mean << " out_nonzero=" << nonZero << "\n";
        }
    }
    return 0;
}

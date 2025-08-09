#include <iostream>
#include <vector>
#include <random>
#include <memory>

#include "Region.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

int main() {
    const int h = 28, w = 28;
    grownet::Region region("image_io");

    int lIn     = region.addInputLayer2D(h, w, 1.0, 0.01);
    int lHidden = region.addLayer(64, 8, 4);
    int lOut    = region.addOutputLayer2D(h, w, 0.2);

    region.bindInput("pixels", { lIn });
    region.connectLayers(lIn, lHidden, 0.05, false);
    region.connectLayers(lHidden, lOut, 0.12, false);

    // Deterministic moving dot pattern (no RNG needed)
    for (int step = 0; step < 20; ++step) {
        std::vector<std::vector<double>> frame(h, std::vector<double>(w, 0.0));
        int y = (step * 2) % h;
        int x = step % w;
        frame[y][x] = 1.0;

        auto m = region.tickImage("pixels", frame); // Metrics struct per your Region

        if ((step + 1) % 5 == 0) {
            auto out = std::dynamic_pointer_cast<grownet::OutputLayer2D>(region.getLayers()[lOut]);
            const auto& img = out->getFrame();
            double sum = 0.0; int nz = 0;
            for (int yy = 0; yy < h; ++yy) {
                for (int xx = 0; xx < w; ++xx) {
                    sum += img[yy][xx];
                    if (img[yy][xx] > 0.05) nz++;
                }
            }
            std::cout << "[" << (step + 1) << "] delivered=" << m.delivered_events
                      << " out_mean=" << (sum / (h * w))
                      << " out_nonzero=" << nz << std::endl;
        }
    }
    return 0;
}

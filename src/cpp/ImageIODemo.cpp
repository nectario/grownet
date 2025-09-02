#include <iostream>
#include <vector>
#include <random>
#include <memory>
#include "Region.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

int main() {
    using namespace grownet;
    const int height = 28, width = 28;
    Region region("image_io");
    int inputLayer   = region.addInputLayer2D(height, width, 1.0, 0.01);
    int hiddenLayer  = region.addLayer(64, 8, 4);
    int outputLayer  = region.addOutputLayer2D(height, width, 0.20);

    region.bindInput("pixels", { inputLayer });
    region.connectLayers(inputLayer, hiddenLayer, 0.05, false);
    region.connectLayers(hiddenLayer, outputLayer, 0.12, false);

    std::mt19937 rng(42);
    std::uniform_real_distribution<double> uni(0.0, 1.0);

    for (int step = 0; step < 20; ++step) {
        std::vector<std::vector<double>> frame(height, std::vector<double>(width, 0.0));
        for (int row = 0; row < height; ++row) {
            for (int col = 0; col < width; ++col) {
                frame[row][col] = (uni(rng) > 0.95) ? 1.0 : 0.0;
            }
        }

        auto tickMetrics = region.tickImage("pixels", frame);

        if ((step + 1) % 5 == 0) {
            auto outLayer = std::dynamic_pointer_cast<OutputLayer2D>(region.getLayers()[outputLayer]);
            const auto& image = outLayer->getFrame();

            double sum = 0.0;
            int nonZero = 0;
            for (int row = 0; row < height; ++row) {
                for (int col = 0; col < width; ++col) {
                    sum += image[row][col];
                    if (image[row][col] > 0.05) nonZero++;
                }
            }
            double mean = sum / (height * width);
            std::cout << "[" << (step + 1) << "] delivered=" << tickMetrics.deliveredEvents
                      << " out_mean=" << mean << " out_nonzero=" << nonZero << "\n";
        }
    }
    return 0;
}

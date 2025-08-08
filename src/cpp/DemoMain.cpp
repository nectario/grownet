#include <iostream>
#include <random>
#include "Layer.h"

using namespace grownet;

int main() {
    Layer layer(50, 10, 5);
    layer.wireRandomFeedforward(0.10);
    layer.wireRandomFeedback(0.01);

    std::mt19937_64 engine{std::random_device{}()};
    std::uniform_real_distribution<double> uniform01{0.0, 1.0};

    for (int stepIndex = 0; stepIndex < 5'000; ++stepIndex) {
        layer.forward(uniform01(engine));

        if ((stepIndex + 1) % 500 == 0) {
            double readinessSum = 0.0;
            double readinessMax = -1e300;
            int neuronCount = 0;
            for (const auto& neuronPtr : layer.getNeurons()) {
                const double readiness = neuronPtr->neuronValue("readiness");
                readinessSum += readiness;
                if (readiness > readinessMax) readinessMax = readiness;
                neuronCount += 1;
            }
            double readinessAvg = neuronCount > 0 ? readinessSum / neuronCount : 0.0;
            std::cout << "[tick " << (stepIndex + 1)
                      << "] readiness avg=" << readinessAvg
                      << " max=" << readinessMax << "\n";
        }
    }

    int totalSlots = 0;
    int totalSynapses = 0;
    for (const auto& neuronPtr : layer.getNeurons()) {
        totalSlots += static_cast<int>(neuronPtr->getSlots().size());
        totalSynapses += static_cast<int>(neuronPtr->getOutgoing().size());
    }

    std::cout << "Finished. totalSlots=" << totalSlots
              << " totalSynapses=" << totalSynapses << std::endl;

    return 0;
}

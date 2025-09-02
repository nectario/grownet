#include <iostream>
#include "Region.h"

int main_demo() {
    grownet::Region region("demo");
    int firstLayer = region.addLayer(8, 2, 1);
    int secondLayer = region.addLayer(8, 2, 1);
    region.bindInput("u", { firstLayer });
    region.connectLayers(firstLayer, secondLayer, 0.2, false);
    auto metrics = region.tick("u", 1.0);
    std::cout << "delivered=" << metrics.deliveredEvents << "\n";
    return 0;
}

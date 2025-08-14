#include <iostream>
#include "Region.h"

int main_demo() {
    grownet::Region region("demo");
    int l1 = region.addLayer(8, 2, 1);
    int l2 = region.addLayer(8, 2, 1);
    region.bindInput("u", { l1 });
    region.connectLayers(l1, l2, 0.2, false);
    auto m = region.tick("u", 1.0);
    std::cout << "delivered=" << m.deliveredEvents << "\n";
    return 0;
}

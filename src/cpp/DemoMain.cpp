#include <iostream>
#include "Region.h"

using namespace grownet;

int main() {
    Region region("demo");
    int l0 = region.addLayer(10, 0, 0);
    int l1 = region.addLayer(10, 0, 0);
    region.bindInput("pixels", {l0});
    region.connectLayers(l0, l1, 0.1, false);

    for (int step = 0; step < 10; ++step) {
        auto m = region.tick("pixels", 1.0);
        if ((step+1) % 2 == 0) {
            std::cout << "[step " << (step+1) << "] delivered=" << m.deliveredEvents
                      << " slots=" << m.totalSlots << " syn=" << m.totalSynapses << "\n";
        }
    }
    return 0;
}

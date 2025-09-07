// Spatial hash grid for proximity neighbor search.
#pragma once
#include <unordered_map>
#include <vector>
#include <cmath>

namespace grownet {

class SpatialHash {
    double cellSize;
    struct Key { int x; int y; int z; };
    struct KeyHash { size_t operator()(const Key& k) const noexcept { return (static_cast<size_t>(k.x) * 73856093u) ^ (static_cast<size_t>(k.y) * 19349663u) ^ (static_cast<size_t>(k.z) * 83492791u); } };
    struct KeyEq { bool operator()(const Key& a, const Key& b) const noexcept { return a.x==b.x && a.y==b.y && a.z==b.z; } };
    std::unordered_map<Key, std::vector<std::pair<int,int>>, KeyHash, KeyEq> cells;
public:
    explicit SpatialHash(double cell) : cellSize(cell) {}
    inline Key keyFor(double x, double y, double z) const { return Key{ static_cast<int>(std::floor(x / cellSize)), static_cast<int>(std::floor(y / cellSize)), static_cast<int>(std::floor(z / cellSize)) }; }
    inline void insert(int layerIndex, int neuronIndex, double x, double y, double z) {
        Key k = keyFor(x,y,z);
        cells[k].emplace_back(layerIndex, neuronIndex);
    }
    inline std::vector<std::pair<int,int>> near(double x, double y, double z) const {
        std::vector<std::pair<int,int>> out;
        Key base = keyFor(x,y,z);
        for (int dz = -1; dz <= 1; ++dz) for (int dy = -1; dy <= 1; ++dy) for (int dx = -1; dx <= 1; ++dx) {
            Key nb{ base.x + dx, base.y + dy, base.z + dz };
            auto it = cells.find(nb);
            if (it != cells.end()) { out.insert(out.end(), it->second.begin(), it->second.end()); }
        }
        return out;
    }
};

} // namespace grownet


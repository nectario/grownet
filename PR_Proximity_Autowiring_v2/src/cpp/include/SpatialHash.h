// File: src/cpp/include/SpatialHash.h
#pragma once
#include <unordered_map>
#include <vector>
#include <tuple>
#include <cmath>

template <typename Item>
class SpatialHash {
public:
    explicit SpatialHash(double cellSize) : cellSize_(cellSize) {}

    void insert(const Item& item, const std::tuple<double,double,double>& pos) {
        auto key = keyForPosition(pos);
        cells_[key].push_back(item);
    }

    std::vector<Item> near(const std::tuple<double,double,double>& pos) const {
        std::vector<Item> result;
        auto base = keyForPosition(pos);
        for (int offsetZ = -1; offsetZ <= 1; ++offsetZ) {
            for (int offsetY = -1; offsetY <= 1; ++offsetY) {
                for (int offsetX = -1; offsetX <= 1; ++offsetX) {
                    Key neighbor{std::get<0>(base)+offsetX, std::get<1>(base)+offsetY, std::get<2>(base)+offsetZ};
                    auto it = cells_.find(neighbor);
                    if (it != cells_.end()) {
                        result.insert(result.end(), it->second.begin(), it->second.end());
                    }
                }
            }
        }
        return result;
    }

private:
    using Key = std::tuple<int,int,int>;
    double cellSize_;
    std::unordered_map<Key, std::vector<Item>> cells_;

    Key keyForPosition(const std::tuple<double,double,double>& pos) const {
        int kx = static_cast<int>(std::floor(std::get<0>(pos) / cellSize_));
        int ky = static_cast<int>(std::floor(std::get<1>(pos) / cellSize_));
        int kz = static_cast<int>(std::floor(std::get<2>(pos) / cellSize_));
        return {kx, ky, kz};
    }
};

#pragma once
#include <vector>
#include <unordered_set>
#include <utility>

namespace grownet {

// Records deterministic windowed geometry for later re‑attach on growth.
class TractWindowed {
public:
  TractWindowed(int sourceLayerIndex,
                int destLayerIndex,
                int kernelH, int kernelW,
                int strideH, int strideW,
                bool samePadding,
                bool destIsOutput2D,
                int destHeight, int destWidth);

  // Enumerate windows and build internal maps from a known source grid size.
  void buildFromSourceGrid(int sourceHeight, int sourceWidth);

  // Called when a source‑layer neuron grows; Region performs actual wiring.
  void attachSourceNeuron(int /*newSourceIndex*/) {}

  // Accessors used by Region:
  bool destinationIsOutput2D() const { return destIsOutput2D_; }
  const std::vector<std::pair<int,int>>& sourceToCenterEdges() const { return sourceCenterEdges_; }
  const std::unordered_set<int>& allowedSourceIndices() const { return allowedSources_; }

  // Geometry helpers (used in tests or debugging)
  bool windowCoversSourceIndex(int sourceIndex) const;

  // Public geometry metadata
  const int sourceLayerIndex;
  const int destLayerIndex;
  const int kernelH;
  const int kernelW;
  const int strideH;
  const int strideW;
  const bool samePadding;
  const bool destIsOutput2D;
  const int destH;
  const int destW;

private:
  std::pair<int,int> centerForWindow(int originRow, int originCol) const;

  std::vector<std::pair<int,int>> sourceCenterEdges_;
  std::unordered_set<int> allowedSources_;
};

} // namespace grownet


#include "TractWindowed.h"
#include <algorithm>

namespace grownet {

TractWindowed::TractWindowed(int s, int d, int kh, int kw, int sh, int sw,
                             bool same, bool destIs2D, int dh, int dw)
  : sourceLayerIndex(s),
    destLayerIndex(d),
    kernelH(kh), kernelW(kw),
    strideH(sh), strideW(sw),
    samePadding(same),
    destIsOutput2D(destIs2D),
    destH(dh), destW(dw) {}

std::pair<int,int> TractWindowed::centerForWindow(int originRow, int originCol) const {
  int centerRow = originRow + kernelH / 2;
  int centerCol = originCol + kernelW / 2;
  if (centerRow < 0) centerRow = 0;
  if (centerCol < 0) centerCol = 0;
  if (centerRow > destH - 1) centerRow = destH - 1;
  if (centerCol > destW - 1) centerCol = destW - 1;
  return {centerRow, centerCol};
}

void TractWindowed::buildFromSourceGrid(int sourceHeight, int sourceWidth) {
  const int padH = samePadding ? kernelH / 2 : 0;
  const int padW = samePadding ? kernelW / 2 : 0;
  const int startRow = samePadding ? -padH : 0;
  const int startCol = samePadding ? -padW : 0;
  const int endRow   = samePadding ? (sourceHeight - 1 + padH) : (sourceHeight - kernelH);
  const int endCol   = samePadding ? (sourceWidth  - 1 + padW) : (sourceWidth  - kernelW);

  std::vector<std::pair<int,int>> tempEdges;
  std::unordered_set<int> tempSources;

  for (int originRow = startRow; originRow <= endRow; originRow += strideH) {
    for (int originCol = startCol; originCol <= endCol; originCol += strideW) {
      const int clipRowStart = std::max(0, originRow);
      const int clipColStart = std::max(0, originCol);
      const int clipRowEnd   = std::min(sourceHeight - 1, originRow + kernelH - 1);
      const int clipColEnd   = std::min(sourceWidth  - 1, originCol + kernelW - 1);
      if (clipRowStart > clipRowEnd || clipColStart > clipColEnd) continue;

      if (destIsOutput2D) {
        const auto center = centerForWindow(originRow, originCol);
        const int centerIndex = center.first * destW + center.second;
        for (int rowIndex = clipRowStart; rowIndex <= clipRowEnd; ++rowIndex) {
          for (int colIndex = clipColStart; colIndex <= clipColEnd; ++colIndex) {
            const int sourceIndex = rowIndex * sourceWidth + colIndex;
            tempEdges.emplace_back(sourceIndex, centerIndex);
            tempSources.insert(sourceIndex);
          }
        }
      } else {
        for (int rowIndex = clipRowStart; rowIndex <= clipRowEnd; ++rowIndex) {
          for (int colIndex = clipColStart; colIndex <= clipColEnd; ++colIndex) {
            const int sourceIndex = rowIndex * sourceWidth + colIndex;
            tempSources.insert(sourceIndex);
          }
        }
      }
    }
  }

  if (destIsOutput2D) {
    std::sort(tempEdges.begin(), tempEdges.end());
    tempEdges.erase(std::unique(tempEdges.begin(), tempEdges.end()), tempEdges.end());
    sourceCenterEdges_.swap(tempEdges);
  } else {
    allowedSources_.swap(tempSources);
  }
}

bool TractWindowed::windowCoversSourceIndex(int sourceIndex) const {
  if (!allowedSources_.empty()) {
    return allowedSources_.count(sourceIndex) > 0;
  }
  if (!destIsOutput2D) return false;
  return std::binary_search(
    sourceCenterEdges_.begin(),
    sourceCenterEdges_.end(),
    std::make_pair(sourceIndex, 0),
    [](const std::pair<int,int>& a, const std::pair<int,int>& b) {
      if (a.first != b.first) return a.first < b.first;
      return a.second < b.second;
    });
}

} // namespace grownet


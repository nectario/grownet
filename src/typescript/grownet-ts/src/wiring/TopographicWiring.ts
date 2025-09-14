export interface TopographicConfig {
  kernelH: number;
  kernelW: number;
  strideH: number;
  strideW: number;
  padding: 'same' | 'valid';
  feedback: boolean;
  weightMode: 'gaussian' | 'dog';
  sigmaCenter: number;
  sigmaSurround: number;
  surroundRatio: number;
  normalizeIncoming: boolean;
}

export function defaultTopographicConfig(): TopographicConfig {
  return {
    kernelH: 7,
    kernelW: 7,
    strideH: 1,
    strideW: 1,
    padding: 'same',
    feedback: false,
    weightMode: 'gaussian',
    sigmaCenter: 2.0,
    sigmaSurround: 4.0,
    surroundRatio: 0.5,
    normalizeIncoming: true,
  };
}

  export function connectLayersTopographic(
    srcHeight: number,
    srcWidth: number,
    dstHeight: number,
    dstWidth: number,
    config: TopographicConfig,
  ): { uniqueSources: number; incomingPerCenter: Array<{ centerRow: number; centerCol: number; weights: Array<{ row: number; col: number; weight: number }> }> } {
  const kernelH = config.kernelH;
  const kernelW = config.kernelW;
  const strideH = config.strideH;
  const strideW = config.strideW;
  const same = config.padding === 'same';

    // Enumerate windows over the source and compute centers in destination domain
    const windows: Array<{ rowStart: number; colStart: number; rowEnd: number; colEnd: number; centerRow: number; centerCol: number }> = [];
    if (same) {
      for (let dstRow = 0; dstRow < dstHeight; dstRow += 1) {
        for (let dstCol = 0; dstCol < dstWidth; dstCol += 1) {
          // compute src window top-left so that center maps to dstRow/dstCol
          const rowStart = Math.max(0, Math.min(srcHeight - kernelH, dstRow - Math.floor(kernelH / 2)));
          const colStart = Math.max(0, Math.min(srcWidth - kernelW, dstCol - Math.floor(kernelW / 2)));
          const rowEnd = Math.min(srcHeight, rowStart + kernelH);
          const colEnd = Math.min(srcWidth, colStart + kernelW);
          windows.push({ rowStart, colStart, rowEnd, colEnd, centerRow: dstRow, centerCol: dstCol });
        }
      }
    } else {
      for (let rowStart = 0; rowStart <= srcHeight - kernelH; rowStart += strideH) {
        for (let colStart = 0; colStart <= srcWidth - kernelW; colStart += strideW) {
          const centerRow = Math.floor(rowStart + kernelH / 2);
          const centerCol = Math.floor(colStart + kernelW / 2);
          windows.push({ rowStart, colStart, rowEnd: rowStart + kernelH, colEnd: colStart + kernelW, centerRow, centerCol });
        }
      }
    }

  // Unique sources
  const covered = new Array<boolean>(srcHeight * srcWidth);
  for (let i = 0; i < covered.length; i += 1) covered[i] = false;
    for (let windowIndex = 0; windowIndex < windows.length; windowIndex += 1) {
      const win = windows[windowIndex];
      for (let row = win.rowStart; row < win.rowEnd; row += 1) {
        for (let col = win.colStart; col < win.colEnd; col += 1) {
          covered[row * srcWidth + col] = true;
        }
      }
    }
  let uniqueSources = 0;
  for (let idx = 0; idx < covered.length; idx += 1) if (covered[idx]) uniqueSources += 1;

  // Build incoming weights per center
    const incomingPerCenter: Array<{ centerRow: number; centerCol: number; weights: Array<{ row: number; col: number; weight: number }> }> = [];
    for (let windowIndex = 0; windowIndex < windows.length; windowIndex += 1) {
      const win = windows[windowIndex];
      const centerRow = Math.max(0, Math.min(dstHeight - 1, win.centerRow));
      const centerCol = Math.max(0, Math.min(dstWidth - 1, win.centerCol));
      const weights: Array<{ row: number; col: number; weight: number }> = [];
      for (let row = win.rowStart; row < win.rowEnd; row += 1) {
        for (let col = win.colStart; col < win.colEnd; col += 1) {
          const deltaRow = row - (win.rowStart + Math.floor(kernelH / 2));
          const deltaCol = col - (win.colStart + Math.floor(kernelW / 2));
          const distanceSq = deltaRow * deltaRow + deltaCol * deltaCol;
          let weightValue = 0.0;
          if (config.weightMode === 'gaussian') {
            weightValue = Math.exp(-distanceSq / (2 * config.sigmaCenter * config.sigmaCenter));
          } else {
            const centerTerm = Math.exp(-distanceSq / (2 * config.sigmaCenter * config.sigmaCenter));
            const surroundTerm = Math.exp(-distanceSq / (2 * config.sigmaSurround * config.sigmaSurround));
            weightValue = Math.max(0, centerTerm - config.surroundRatio * surroundTerm);
          }
          weights.push({ row, col, weight: weightValue });
        }
      }
      if (config.normalizeIncoming) {
        let sumWeights = 0;
        for (let i = 0; i < weights.length; i += 1) sumWeights += weights[i].weight;
        const eps = 1e-12;
        const denom = sumWeights > eps ? sumWeights : 1.0;
        for (let i = 0; i < weights.length; i += 1) weights[i].weight = weights[i].weight / denom;
      }
      incomingPerCenter.push({ centerRow, centerCol, weights });
    }
  return { uniqueSources, incomingPerCenter };
}


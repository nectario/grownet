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
): { uniqueSources: number; incomingPerCenter: Array<{ centerRow: number; centerCol: number; weights: Array<{ row: number; col: number; w: number }> }> } {
  const kernelH = config.kernelH;
  const kernelW = config.kernelW;
  const strideH = config.strideH;
  const strideW = config.strideW;
  const same = config.padding === 'same';

  // Enumerate windows over the source and compute centers in destination domain
  const windows: Array<{ r0: number; c0: number; r1: number; c1: number; centerR: number; centerC: number }> = [];
  if (same) {
    for (let dstR = 0; dstR < dstHeight; dstR += 1) {
      for (let dstC = 0; dstC < dstWidth; dstC += 1) {
        // compute src window top-left so that center maps to dstR/dstC
        const r0 = Math.max(0, Math.min(srcHeight - kernelH, dstR - Math.floor(kernelH / 2)));
        const c0 = Math.max(0, Math.min(srcWidth - kernelW, dstC - Math.floor(kernelW / 2)));
        const r1 = Math.min(srcHeight, r0 + kernelH);
        const c1 = Math.min(srcWidth, c0 + kernelW);
        windows.push({ r0, c0, r1, c1, centerR: dstR, centerC: dstC });
      }
    }
  } else {
    for (let r0 = 0; r0 <= srcHeight - kernelH; r0 += strideH) {
      for (let c0 = 0; c0 <= srcWidth - kernelW; c0 += strideW) {
        const centerR = Math.floor(r0 + kernelH / 2);
        const centerC = Math.floor(c0 + kernelW / 2);
        windows.push({ r0, c0, r1: r0 + kernelH, c1: c0 + kernelW, centerR, centerC });
      }
    }
  }

  // Unique sources
  const covered = new Array<boolean>(srcHeight * srcWidth);
  for (let i = 0; i < covered.length; i += 1) covered[i] = false;
  for (let w = 0; w < windows.length; w += 1) {
    const win = windows[w];
    for (let r = win.r0; r < win.r1; r += 1) for (let c = win.c0; c < win.c1; c += 1) covered[r * srcWidth + c] = true;
  }
  let uniqueSources = 0;
  for (let idx = 0; idx < covered.length; idx += 1) if (covered[idx]) uniqueSources += 1;

  // Build incoming weights per center
  const incomingPerCenter: Array<{ centerRow: number; centerCol: number; weights: Array<{ row: number; col: number; w: number }> }> = [];
  for (let w = 0; w < windows.length; w += 1) {
    const win = windows[w];
    const centerRow = Math.max(0, Math.min(dstHeight - 1, win.centerR));
    const centerCol = Math.max(0, Math.min(dstWidth - 1, win.centerC));
    const weights: Array<{ row: number; col: number; w: number }> = [];
    for (let r = win.r0; r < win.r1; r += 1) {
      for (let c = win.c0; c < win.c1; c += 1) {
        const dr = r - (win.r0 + Math.floor(kernelH / 2));
        const dc = c - (win.c0 + Math.floor(kernelW / 2));
        const distanceSq = dr * dr + dc * dc;
        let wval = 0.0;
        if (config.weightMode === 'gaussian') {
          wval = Math.exp(-distanceSq / (2 * config.sigmaCenter * config.sigmaCenter));
        } else {
          const centerTerm = Math.exp(-distanceSq / (2 * config.sigmaCenter * config.sigmaCenter));
          const surroundTerm = Math.exp(-distanceSq / (2 * config.sigmaSurround * config.sigmaSurround));
          wval = Math.max(0, centerTerm - config.surroundRatio * surroundTerm);
        }
        weights.push({ row: r, col: c, w: wval });
      }
    }
    if (config.normalizeIncoming) {
      let s = 0;
      for (let i = 0; i < weights.length; i += 1) s += weights[i].w;
      const eps = 1e-12;
      const denom = s > eps ? s : 1.0;
      for (let i = 0; i < weights.length; i += 1) weights[i].w = weights[i].w / denom;
    }
    incomingPerCenter.push({ centerRow, centerCol, weights });
  }
  return { uniqueSources, incomingPerCenter };
}


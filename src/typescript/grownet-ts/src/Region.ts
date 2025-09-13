import { RegionMetrics } from './metrics/RegionMetrics.js';
import { ParallelOptions } from './pal/index.js';

export class Region {
  private name: string;
  private layers2d: Array<{ id: number; type: 'input' | 'output'; height: number; width: number; gain?: number; epsilonFire?: number; smoothing?: number }> = [];
  private nextLayerId: number = 0;
  private inputBindings: Map<string, number[]> = new Map();

  constructor(name: string) {
    this.name = name;
  }

  addInputLayer2D(height: number, width: number, gain: number, epsilonFire: number): number {
    const id = this.nextLayerId++;
    this.layers2d.push({ id, type: 'input', height, width, gain, epsilonFire });
    return id;
  }

  addOutputLayer2D(height: number, width: number, smoothing: number): number {
    const id = this.nextLayerId++;
    this.layers2d.push({ id, type: 'output', height, width, smoothing });
    return id;
  }

  bindInput(portName: string, layerIndices: number[]): void {
    this.inputBindings.set(portName, [...layerIndices]);
  }

  connectLayersWindowed(
    srcLayerId: number,
    dstLayerId: number,
    kernelHeight: number,
    kernelWidth: number,
    strideHeight: number,
    strideWidth: number,
    padding: string,
    feedback: boolean,
  ): number {
    (void)dstLayerId; (void)feedback;
    const src = this.layers2d.find((l) => l.id === srcLayerId);
    if (!src) return 0;
    const height = src.height; const width = src.width;
    if (padding.toLowerCase() === 'same') return height * width;
    // VALID padding: compute union coverage of all valid windows
    const rowStartOffsets: number[] = [];
    const colStartOffsets: number[] = [];
    for (let startRowOffset = 0; startRowOffset <= height - kernelHeight; startRowOffset += strideHeight) rowStartOffsets.push(startRowOffset);
    for (let startColOffset = 0; startColOffset <= width - kernelWidth; startColOffset += strideWidth) colStartOffsets.push(startColOffset);
    const coveredIndices = new Array<boolean>(height * width);
    for (let coveredIndex = 0; coveredIndex < coveredIndices.length; coveredIndex += 1) coveredIndices[coveredIndex] = false;
    for (let rowStartListIndex = 0; rowStartListIndex < rowStartOffsets.length; rowStartListIndex += 1) {
      const windowStartRow = rowStartOffsets[rowStartListIndex];
      for (let colStartListIndex = 0; colStartListIndex < colStartOffsets.length; colStartListIndex += 1) {
        const windowStartCol = colStartOffsets[colStartListIndex];
        for (let kernelRowOffset = 0; kernelRowOffset < kernelHeight; kernelRowOffset += 1) {
          for (let kernelColOffset = 0; kernelColOffset < kernelWidth; kernelColOffset += 1) {
            const rowIndex = windowStartRow + kernelRowOffset; const colIndex = windowStartCol + kernelColOffset;
            coveredIndices[rowIndex * width + colIndex] = true;
          }
        }
      }
    }
    let uniqueSourcesCount = 0;
    for (let coveredIndex = 0; coveredIndex < coveredIndices.length; coveredIndex += 1) if (coveredIndices[coveredIndex]) uniqueSourcesCount += 1;
    return uniqueSourcesCount;
  }

  computeSpatialMetrics(
    image2d:
      | number[][]
      | Float64Array
      | { data: Float64Array; height: number; width: number },
    preferOutput: boolean,
  ): RegionMetrics {
    const parsed = this.parseImage2D(image2d);
    const height = parsed.height;
    const width = parsed.width;
    const data = parsed.data;

    let activePixels = 0;
    let sum = 0.0;
    let rowSum = 0.0;
    let colSum = 0.0;
    let rowMin = Number.POSITIVE_INFINITY;
    let rowMax = Number.NEGATIVE_INFINITY;
    let colMin = Number.POSITIVE_INFINITY;
    let colMax = Number.NEGATIVE_INFINITY;

    for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
      for (let colIndex = 0; colIndex < width; colIndex += 1) {
        const idx = rowIndex * width + colIndex;
        const value = data[idx];
        if (value > 0) {
          activePixels += 1;
          sum += value;
          rowSum += value * rowIndex;
          colSum += value * colIndex;
          if (rowIndex < rowMin) rowMin = rowIndex;
          if (rowIndex > rowMax) rowMax = rowIndex;
          if (colIndex < colMin) colMin = colIndex;
          if (colIndex > colMax) colMax = colIndex;
        }
      }
    }

    const deliveredEvents = activePixels > 0 ? 1 : 0;
    const totalSlots = height * width;
    const totalSynapses = 0;
    const centroidRow = activePixels > 0 ? (sum > 0 ? rowSum / sum : rowSum / activePixels) : 0;
    const centroidCol = activePixels > 0 ? (sum > 0 ? colSum / sum : colSum / activePixels) : 0;
    const bboxRowMin = activePixels > 0 ? Math.floor(rowMin) : -1;
    const bboxRowMax = activePixels > 0 ? Math.floor(rowMax) : -1;
    const bboxColMin = activePixels > 0 ? Math.floor(colMin) : -1;
    const bboxColMax = activePixels > 0 ? Math.floor(colMax) : -1;

    // preferOutput is accepted for parity; this minimal implementation ignores the flag.
    (void)preferOutput;

    return new RegionMetrics(
      deliveredEvents,
      totalSlots,
      totalSynapses,
      activePixels,
      centroidRow,
      centroidCol,
      bboxRowMin,
      bboxRowMax,
      bboxColMin,
      bboxColMax,
    );
  }

  tickND(
    port: string,
    tensor: number[] | number[][] | number[][][],
    options?: ParallelOptions,
  ): RegionMetrics {
    (void)port;
    (void)options;
    const flat = this.flattenTensor(tensor);
    let active = 0;
    for (let index = 0; index < flat.length; index += 1) if (flat[index] > 0) active += 1;
    const deliveredEvents = active;
    const totalSlots = flat.length;
    return new RegionMetrics(
      deliveredEvents,
      totalSlots,
      0,
      active,
      0,
      0,
      -1,
      -1,
      -1,
      -1,
    );
  }
  
  tick2D(port: string, image2d: number[][]): RegionMetrics {
    // Basic wrapper using ND path
    return this.tickND(port, image2d);
  }

  private parseImage2D(
    image2d: number[][] | Float64Array | { data: Float64Array; height: number; width: number },
  ): { data: Float64Array; height: number; width: number } {
    if (Array.isArray(image2d)) {
      const height = image2d.length;
      const width = height > 0 ? image2d[0].length : 0;
      const data = new Float64Array(height * width);
      for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
        const row = image2d[rowIndex];
        for (let colIndex = 0; colIndex < width; colIndex += 1) {
          data[rowIndex * width + colIndex] = row[colIndex] ?? 0;
        }
      }
      return { data, height, width };
    }
    if (image2d instanceof Float64Array) {
      const side = Math.sqrt(image2d.length);
      const height = Math.floor(side);
      const width = height;
      return { data: image2d, height, width };
    }
    return { data: image2d.data, height: image2d.height, width: image2d.width };
  }

  private flattenTensor(tensor: number[] | number[][] | number[][][]): number[] {
    if (!Array.isArray(tensor)) return [];
    const out: number[] = [];
    function visit(node: number | number[] | number[][]): void {
      if (Array.isArray(node)) {
        for (let index = 0; index < node.length; index += 1) visit(node[index] as number | number[]);
      } else {
        out.push(node);
      }
    }
    visit(tensor as number[] | number[][]);
    return out;
  }
}
import { RegionMetrics } from './metrics/RegionMetrics.js';

import { RegionMetrics } from './metrics/RegionMetrics.js';
import { ParallelOptions } from './pal/index.js';

export class Region {
  private name: string;

  constructor(name: string) {
    this.name = name;
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


import { RegionMetrics } from './metrics/RegionMetrics.js';
import { ParallelOptions } from './pal/index.js';
import { Layer, LayerKind } from './core/Layer.js';
import { Tract } from './core/Tract.js';

export class Region {
  private name: string;
  private layers: Array<Layer> = [];
  private nextLayerId: number = 0;
  private inputBindings: Map<string, number[]> = new Map();
  private tracts: Array<Tract> = [];
  private growthPolicy: { enableLayerGrowth: boolean; maxLayers: number; avgSlotsThreshold: number; percentNeuronsAtCapacityThreshold?: number; layerCooldownTicks: number; rngSeed: number } | null = null;
  private lastLayerGrowthStep: number = -1;

  constructor(name: string) {
    this.name = name;
  }

  addInputLayer2D(height: number, width: number, gain: number, epsilonFire: number): number {
    const layerId = this.nextLayerId++;
    const layer = new Layer(`input2d_${layerId}`, LayerKind.Input2D, height, width);
    this.layers.push(layer);
    return layerId;
  }

  addOutputLayer2D(height: number, width: number, smoothing: number): number {
    const layerId = this.nextLayerId++;
    const layer = new Layer(`output2d_${layerId}`, LayerKind.Output2D, height, width);
    this.layers.push(layer);
    return layerId;
  }

  bindInput(portName: string, layerIndices: number[]): void {
    this.inputBindings.set(portName, [...layerIndices]);
  }

  setGrowthPolicy(policy: { enableLayerGrowth: boolean; maxLayers: number; avgSlotsThreshold: number; percentNeuronsAtCapacityThreshold?: number; layerCooldownTicks: number; rngSeed: number }): void {
    this.growthPolicy = policy;
  }

  getGrowthPolicy(): { enableLayerGrowth: boolean; maxLayers: number; avgSlotsThreshold: number; percentNeuronsAtCapacityThreshold?: number; layerCooldownTicks: number; rngSeed: number } | null {
    return this.growthPolicy;
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
    const srcLayer = this.layers[srcLayerId];
    const dstLayer = this.layers[dstLayerId];
    if (!srcLayer || !dstLayer) return 0;
    const srcHeight = srcLayer.getHeight();
    const srcWidth = srcLayer.getWidth();
    const dstHeight = dstLayer.getHeight();
    const dstWidth = dstLayer.getWidth();
    const isSame = padding.toLowerCase() === 'same';
    const rowStartOffsets: number[] = [];
    const colStartOffsets: number[] = [];
    if (isSame) {
      // Enumerate destination centers and infer source windows
      for (let dstRow = 0; dstRow < dstHeight; dstRow += 1) rowStartOffsets.push(dstRow);
      for (let dstCol = 0; dstCol < dstWidth; dstCol += 1) colStartOffsets.push(dstCol);
    } else {
      for (let r0 = 0; r0 <= srcHeight - kernelHeight; r0 += strideHeight) rowStartOffsets.push(r0);
      for (let c0 = 0; c0 <= srcWidth - kernelWidth; c0 += strideWidth) colStartOffsets.push(c0);
    }
    const coveredIndices = new Array<boolean>(srcHeight * srcWidth);
    for (let coveredIndex = 0; coveredIndex < coveredIndices.length; coveredIndex += 1) coveredIndices[coveredIndex] = false;
    const centerMap = new Map<number, number>();
    const srcNeurons = srcLayer.getNeurons();
    const dstNeurons = dstLayer.getNeurons();
    const connections = new Set<string>();
    if (isSame) {
      for (let dstRow = 0; dstRow < dstHeight; dstRow += 1) {
        for (let dstCol = 0; dstCol < dstWidth; dstCol += 1) {
          const r0 = Math.max(0, Math.min(srcHeight - kernelHeight, dstRow - Math.floor(kernelHeight / 2)));
          const c0 = Math.max(0, Math.min(srcWidth - kernelWidth, dstCol - Math.floor(kernelWidth / 2)));
          const r1 = Math.min(srcHeight, r0 + kernelHeight);
          const c1 = Math.min(srcWidth, c0 + kernelWidth);
          const centerIndex = dstLayer.indexAt(dstRow, dstCol);
          for (let r = r0; r < r1; r += 1) {
            for (let c = c0; c < c1; c += 1) {
              const srcIndex = srcLayer.indexAt(r, c);
              coveredIndices[srcIndex] = true;
              centerMap.set(srcIndex, centerIndex);
              const key = `${srcIndex}->${centerIndex}`;
              if (!connections.has(key)) {
                srcNeurons[srcIndex].connect(dstNeurons[centerIndex], feedback);
                connections.add(key);
              }
            }
          }
        }
      }
    } else {
      for (let r0Index = 0; r0Index < rowStartOffsets.length; r0Index += 1) {
        const r0 = rowStartOffsets[r0Index];
        for (let c0Index = 0; c0Index < colStartOffsets.length; c0Index += 1) {
          const c0 = colStartOffsets[c0Index];
          const r1 = r0 + kernelHeight;
          const c1 = c0 + kernelWidth;
          const centerRow = Math.floor(r0 + kernelHeight / 2);
          const centerCol = Math.floor(c0 + kernelWidth / 2);
          const centerIndex = dstLayer.indexAt(centerRow, centerCol);
          for (let r = r0; r < r1; r += 1) {
            for (let c = c0; c < c1; c += 1) {
              const srcIndex = srcLayer.indexAt(r, c);
              coveredIndices[srcIndex] = true;
              centerMap.set(srcIndex, centerIndex);
              const key = `${srcIndex}->${centerIndex}`;
              if (!connections.has(key)) {
                srcNeurons[srcIndex].connect(dstNeurons[centerIndex], feedback);
                connections.add(key);
              }
            }
          }
        }
      }
    }
    const tract = new Tract(srcLayer, dstLayer, feedback);
    tract.setCenterMap(centerMap);
    this.tracts.push(tract);
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
    void preferOutput;

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
    void options;
    const boundLayers = this.inputBindings.get(port) || [];
    const tensor2d = Array.isArray(tensor[0]) ? (tensor as number[][]) : [tensor as number[]];
    let deliveredEvents = 0;
    let totalSlots = 0;
    for (let bindIndex = 0; bindIndex < boundLayers.length; bindIndex += 1) {
      const layerIndex = boundLayers[bindIndex];
      const layer = this.layers[layerIndex];
      if (!layer) continue;
      const height = layer.getHeight();
      const width = layer.getWidth();
      const neurons = layer.getNeurons();
      totalSlots += neurons.length;
      for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
        const row = tensor2d[rowIndex] || [];
        for (let colIndex = 0; colIndex < width; colIndex += 1) {
          const value = row[colIndex] || 0;
          if (value <= 0) continue;
          const idx = layer.indexAt(rowIndex, colIndex);
          const fired = neurons[idx].onInput2D(value, rowIndex, colIndex);
          if (fired) { deliveredEvents += 1; neurons[idx].onOutput(value); }
        }
      }
    }
    // Output metrics (scan output2d layers)
    let activePixels = 0;
    let sum = 0.0;
    let rowSum = 0.0;
    let colSum = 0.0;
    let rowMin = Number.POSITIVE_INFINITY;
    let rowMax = Number.NEGATIVE_INFINITY;
    let colMin = Number.POSITIVE_INFINITY;
    let colMax = Number.NEGATIVE_INFINITY;
    for (let layerIndex = 0; layerIndex < this.layers.length; layerIndex += 1) {
      const layer = this.layers[layerIndex];
      if (layer.getKind() !== LayerKind.Output2D) continue;
      const height = layer.getHeight();
      const width = layer.getWidth();
      const neurons = layer.getNeurons();
      for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
        for (let colIndex = 0; colIndex < width; colIndex += 1) {
          const idx = layer.indexAt(rowIndex, colIndex);
          const neuron = neurons[idx];
          if (neuron && neuron.getFiredLast() === true) {
            activePixels += 1;
            const value = 1.0;
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
    }

    // Phase B: end tick + growth check (one growth per tick)
    for (let i = 0; i < this.layers.length; i += 1) this.layers[i].endTick();
    if (this.growthPolicy) {
      const policy = this.growthPolicy;
      const currentStep = (this.layers[0]?.getBus().getCurrentStep()) || 0;
      let growthDone = false;
      for (let li = 0; li < this.layers.length && !growthDone; li += 1) {
        const neurons = this.layers[li].getNeurons();
        for (let ni = 0; ni < neurons.length && !growthDone; ni += 1) {
          const neuron = neurons[ni];
          if (neuron.getFallbackStreak() >= 3) {
            const last = neuron.getLastGrowthTick();
            if (currentStep - last >= (policy.layerCooldownTicks || 100)) {
              const newIndex = this.layers[li].tryGrowNeuron(ni);
              if (newIndex >= 0) {
                // Autowire new neuron for tracts where this layer is source
                for (let ti = 0; ti < this.tracts.length; ti += 1) {
                  const t = this.tracts[ti];
                  if (t.getSource() === this.layers[li]) t.attachSourceNeuron(newIndex);
                }
                neuron.setLastGrowthTick(currentStep);
                growthDone = true;
                this.lastLayerGrowthStep = currentStep;
              }
            }
          }
        }
      }
    }
    return new RegionMetrics(
      deliveredEvents,
      totalSlots,
      0,
      activePixels,
      sum > 0 ? rowSum / sum : 0,
      sum > 0 ? colSum / sum : 0,
      activePixels > 0 ? Math.floor(rowMin) : -1,
      activePixels > 0 ? Math.floor(rowMax) : -1,
      activePixels > 0 ? Math.floor(colMin) : -1,
      activePixels > 0 ? Math.floor(colMax) : -1,
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

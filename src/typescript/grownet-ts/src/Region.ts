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
  // Mesh rules for deterministic autowiring on neuron growth
  private meshRules: Array<{ src: number; dst: number; prob: number; feedback: boolean }> = [];
  // Simple deterministic RNG (LCG) for wiring reproducibility
  private rngState: number = 1234;

  constructor(name: string) {
    this.name = name;
  }

  private rand(): number {
    // LCG: constants from Numerical Recipes
    this.rngState = (1664525 * this.rngState + 1013904223) >>> 0;
    return (this.rngState & 0xffffffff) / 0x100000000;
  }

  private isTrainable(kind: LayerKind): boolean {
    return kind !== LayerKind.Input2D && kind !== LayerKind.Output2D;
  }

  addLayer(excitatoryCount: number): number {
    const layerId = this.nextLayerId++;
    const layer = new Layer(`layer_${layerId}`, LayerKind.Generic);
    layer.addNeurons(Math.max(0, Math.floor(excitatoryCount)));
    try { (layer as unknown as { setRegion?: (r: Region) => void }).setRegion?.(this); } catch {}
    this.layers.push(layer);
    return layerId;
  }

  addInputLayer2D(height: number, width: number, gain: number, epsilonFire: number): number {
    void gain;
    void epsilonFire;
    const layerId = this.nextLayerId++;
    const layer = new Layer(`input2d_${layerId}`, LayerKind.Input2D, height, width);
    try { (layer as unknown as { setRegion?: (r: Region) => void }).setRegion?.(this); } catch {}
    this.layers.push(layer);
    return layerId;
  }

  addOutputLayer2D(height: number, width: number, smoothing: number): number {
    void smoothing;
    const layerId = this.nextLayerId++;
    const layer = new Layer(`output2d_${layerId}`, LayerKind.Output2D, height, width);
    try { (layer as unknown as { setRegion?: (r: Region) => void }).setRegion?.(this); } catch {}
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

  connectLayers(sourceIndex: number, destIndex: number, probability: number, feedback: boolean): number {
    const src = this.layers[sourceIndex];
    const dst = this.layers[destIndex];
    if (!src || !dst) return 0;
    const prob = Math.max(0, Math.min(1, probability));
    const srcNeurons = src.getNeurons();
    const dstNeurons = dst.getNeurons();
    let edges = 0;
    for (let sourceIndexIter = 0; sourceIndexIter < srcNeurons.length; sourceIndexIter += 1) {
      for (let destIndexIter = 0; destIndexIter < dstNeurons.length; destIndexIter += 1) {
        if (this.rand() <= prob) {
          srcNeurons[sourceIndexIter].connect(dstNeurons[destIndexIter], feedback);
          edges += 1;
        }
      }
    }
    this.meshRules.push({ src: sourceIndex, dst: destIndex, prob, feedback });
    return edges;
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
      for (let rowStart = 0; rowStart <= srcHeight - kernelHeight; rowStart += strideHeight)
        rowStartOffsets.push(rowStart);
      for (let colStart = 0; colStart <= srcWidth - kernelWidth; colStart += strideWidth)
        colStartOffsets.push(colStart);
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
          const rowStart = Math.max(0, Math.min(srcHeight - kernelHeight, dstRow - Math.floor(kernelHeight / 2)));
          const colStart = Math.max(0, Math.min(srcWidth - kernelWidth, dstCol - Math.floor(kernelWidth / 2)));
          const rowEnd = Math.min(srcHeight, rowStart + kernelHeight);
          const colEnd = Math.min(srcWidth, colStart + kernelWidth);
          const centerIndex = dstLayer.indexAt(dstRow, dstCol);
          const dstNeuron = dstNeurons[centerIndex];
          if (!dstNeuron) continue;
          for (let row = rowStart; row < rowEnd; row += 1) {
            for (let col = colStart; col < colEnd; col += 1) {
              const srcIndex = srcLayer.indexAt(row, col);
              coveredIndices[srcIndex] = true;
              centerMap.set(srcIndex, centerIndex);
              const key = `${srcIndex}->${centerIndex}`;
              if (!connections.has(key)) {
                const srcNeuron = srcNeurons[srcIndex];
                if (srcNeuron) {
                  srcNeuron.connect(dstNeuron, feedback);
                  connections.add(key);
                }
              }
            }
          }
        }
      }
    } else {
      for (const rowStart of rowStartOffsets) {
        for (const colStart of colStartOffsets) {
          const rowEnd = rowStart + kernelHeight;
          const colEnd = colStart + kernelWidth;
          const centerRow = Math.floor(rowStart + kernelHeight / 2);
          const centerCol = Math.floor(colStart + kernelWidth / 2);
          const centerIndex = dstLayer.indexAt(centerRow, centerCol);
          const dstNeuron = dstNeurons[centerIndex];
          if (!dstNeuron) continue;
          for (let row = rowStart; row < rowEnd; row += 1) {
            for (let col = colStart; col < colEnd; col += 1) {
              const srcIndex = srcLayer.indexAt(row, col);
              coveredIndices[srcIndex] = true;
              centerMap.set(srcIndex, centerIndex);
              const key = `${srcIndex}->${centerIndex}`;
              if (!connections.has(key)) {
                const srcNeuron = srcNeurons[srcIndex];
                if (srcNeuron) {
                  srcNeuron.connect(dstNeuron, feedback);
                  connections.add(key);
                }
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
    for (const covered of coveredIndices) if (covered) uniqueSourcesCount += 1;
    return uniqueSourcesCount;
  }

  private autowireNewNeuron(layerIndex: number, newIdx: number): void {
    // Outbound mesh
    for (let ruleIndex = 0; ruleIndex < this.meshRules.length; ruleIndex += 1) {
      const rule = this.meshRules[ruleIndex];
      if (rule.src !== layerIndex) continue;
      const srcLayer = this.layers[layerIndex];
      const dstLayer = this.layers[rule.dst];
      if (!srcLayer || !dstLayer) continue;
      const sourceNeuron = srcLayer.getNeurons()[newIdx];
      const targets = dstLayer.getNeurons();
      for (let targetIndex = 0; targetIndex < targets.length; targetIndex += 1) {
        if (this.rand() <= rule.prob) sourceNeuron.connect(targets[targetIndex], rule.feedback);
      }
    }
    // Inbound mesh
    for (let ruleIndex = 0; ruleIndex < this.meshRules.length; ruleIndex += 1) {
      const rule = this.meshRules[ruleIndex];
      if (rule.dst !== layerIndex) continue;
      const srcLayer = this.layers[rule.src];
      const dstLayer = this.layers[layerIndex];
      if (!srcLayer || !dstLayer) continue;
      const targetNeuron = dstLayer.getNeurons()[newIdx];
      const sources = srcLayer.getNeurons();
      for (let sourceIndexIter = 0; sourceIndexIter < sources.length; sourceIndexIter += 1) {
        if (this.rand() <= rule.prob) sources[sourceIndexIter].connect(targetNeuron, rule.feedback);
      }
    }
    // Tracts where layer is source
    for (let tractIndex = 0; tractIndex < this.tracts.length; tractIndex += 1) {
      const tr = this.tracts[tractIndex];
      if (tr.getSource() === this.layers[layerIndex]) tr.attachSourceNeuron(newIdx);
    }
  }

  autowireNewNeuronByRef(layerRef: Layer, newIdx: number): void {
    const idx = this.layers.indexOf(layerRef);
    if (idx >= 0) this.autowireNewNeuron(idx, newIdx);
  }

  requestLayerGrowth(saturatedLayerIndex: number, connectionProbability: number = 1.0): number {
    if (saturatedLayerIndex < 0 || saturatedLayerIndex >= this.layers.length) return -1;
    const newIdx = this.addLayer(4); // small spillover layer
    this.connectLayers(saturatedLayerIndex, newIdx, connectionProbability, false);
    return newIdx;
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
        const value = data[idx] ?? 0;
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
    const tensor2d = Array.isArray((tensor as number[] | number[][])[0])
      ? (tensor as number[][])
      : [tensor as number[]];
    let boundLayers = this.inputBindings.get(port);
    if (!boundLayers || boundLayers.length === 0) {
      const height = tensor2d.length;
      const width = tensor2d[0]?.length ?? 0;
      const layerId = this.addInputLayer2D(height, width, 1.0, 0.0);
      this.bindInput(port, [layerId]);
      boundLayers = [layerId];
    }
    let deliveredEvents = 0;
    let totalSlots = 0;
    for (const layerIndex of boundLayers) {
      if (layerIndex === undefined) continue;
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
          const neuron = neurons[idx];
          if (!neuron) continue;
          const fired = neuron.onInput2D(value, rowIndex, colIndex);
          if (fired) { deliveredEvents += 1; neuron.onOutput(value); }
        }
      }
    }
    // Output metrics (scan output2d layers) using accumulated amplitudes
    let activePixels = 0;
    let sum = 0.0;
    let rowSum = 0.0;
    let colSum = 0.0;
    let rowMin = Number.POSITIVE_INFINITY;
    let rowMax = Number.NEGATIVE_INFINITY;
    let colMin = Number.POSITIVE_INFINITY;
    let colMax = Number.NEGATIVE_INFINITY;
    for (const layer of this.layers) {
      if (!layer || layer.getKind() !== LayerKind.Output2D) continue;
      const height = layer.getHeight();
      const width = layer.getWidth();
      const neurons = layer.getNeurons();
      for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
        for (let colIndex = 0; colIndex < width; colIndex += 1) {
          const idx = layer.indexAt(rowIndex, colIndex);
          const neuron = neurons[idx];
          if (neuron) {
            const value = (neuron as unknown as { getAccumulatedAmplitude: () => number }).getAccumulatedAmplitude?.() ?? 0.0;
            if (value > 0) {
              activePixels += 1;
              sum += value;
              rowSum += value * rowIndex;
              colSum += value * colIndex;
            }
            if (rowIndex < rowMin) rowMin = rowIndex;
            if (rowIndex > rowMax) rowMax = rowIndex;
            if (colIndex < colMin) colMin = colIndex;
            if (colIndex > colMax) colMax = colIndex;
          }
        }
      }
    }

    // Phase B: end tick + region growth check (one growth per tick)
    for (let layerIndexIter = 0; layerIndexIter < this.layers.length; layerIndexIter += 1) this.layers[layerIndexIter].endTick();
    if (this.growthPolicy && this.growthPolicy.enableLayerGrowth) {
      const policy = this.growthPolicy;
      const currentStep = (this.layers[0]?.getBus().getCurrentStep()) || 0;
      if (policy.maxLayers <= 0 || this.layers.length < policy.maxLayers) {
        if (this.lastLayerGrowthStep < 0 || (currentStep - this.lastLayerGrowthStep) >= (policy.layerCooldownTicks || 0)) {
          // Compute region pressure
          let totalNeurons = 0;
          let totalSlotsRegion = 0;
          let atCapWithFallback = 0;
          for (let layerScanIndex = 0; layerScanIndex < this.layers.length; layerScanIndex += 1) {
            const layer = this.layers[layerScanIndex];
            const neurons = layer.getNeurons();
            for (let neuronScanIndex = 0; neuronScanIndex < neurons.length; neuronScanIndex += 1) {
              const n = neurons[neuronScanIndex] as unknown as {
                getSlotLimit: () => number;
                getLastSlotUsedFallback: () => boolean;
                getSlotsCount: () => number;
              };
              totalNeurons += 1;
              const slotsCount = (n.getSlotsCount && typeof n.getSlotsCount === 'function') ? n.getSlotsCount() : 0;
              totalSlotsRegion += slotsCount;
              const cap = (n.getSlotLimit && typeof n.getSlotLimit === 'function') ? n.getSlotLimit() : -1;
              const usedFallback = (n.getLastSlotUsedFallback && typeof n.getLastSlotUsedFallback === 'function') ? n.getLastSlotUsedFallback() : false;
              const atCap = (cap >= 0) && (slotsCount >= cap);
              if (atCap && usedFallback) atCapWithFallback += 1;
            }
          }
          const avgSlots = totalNeurons > 0 ? (totalSlotsRegion / totalNeurons) : 0;
          const pct = totalNeurons > 0 ? (100.0 * atCapWithFallback / totalNeurons) : 0;
          const avgOk = avgSlots >= policy.avgSlotsThreshold;
          const pctOk = (policy.percentNeuronsAtCapacityThreshold ?? 0) > 0 && pct >= (policy.percentNeuronsAtCapacityThreshold ?? 0);
          if (avgOk || pctOk) {
            // Choose donor: last trainable layer
            let donor = -1;
            for (let layerReverseIndex = this.layers.length - 1; layerReverseIndex >= 0; layerReverseIndex -= 1) {
              if (this.isTrainable(this.layers[layerReverseIndex].getKind())) { donor = layerReverseIndex; break; }
            }
            if (donor >= 0) {
              const newIndex = this.requestLayerGrowth(donor, 1.0);
              if (newIndex >= 0) this.lastLayerGrowthStep = currentStep;
            }
          }
        }
      }
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
        const width = height > 0 ? (image2d[0]?.length ?? 0) : 0;
      const data = new Float64Array(height * width);
        for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
          const row = image2d[rowIndex] || [];
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

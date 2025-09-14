import { LateralBus } from './LateralBus.js';
import { Neuron } from './Neuron.js';
import { SlotConfig, fixedSlotConfig } from './SlotConfig.js';

export enum LayerKind { Generic = 'generic', Input2D = 'input2d', Output2D = 'output2d' }

export class Layer {
  private name: string;
  private kind: LayerKind;
  private height: number;
  private width: number;
  private bus: LateralBus;
  private neurons: Array<Neuron> = [];
  private neuronLimit: number;
  private slotConfig: SlotConfig;
  private regionRef: unknown | undefined;

  constructor(name: string, kind: LayerKind, height?: number, width?: number, slotConfig?: SlotConfig) {
    this.name = name;
    this.kind = kind;
    this.height = typeof height === 'number' ? height : 0;
    this.width = typeof width === 'number' ? width : 0;
    this.bus = new LateralBus(0.9);
    this.slotConfig = slotConfig || fixedSlotConfig(5.0);
    this.neuronLimit = -1;
    if (kind === LayerKind.Input2D || kind === LayerKind.Output2D) {
      const count = this.height * this.width;
      for (let index = 0; index < count; index += 1) {
        const neuron = new Neuron(`${name}.${index}`, this.bus, this.slotConfig);
        this.neurons.push(neuron);
      }
    }
  }

  getKind(): LayerKind { return this.kind; }
  getHeight(): number { return this.height; }
  getWidth(): number { return this.width; }
  getNeurons(): Array<Neuron> { return this.neurons; }
  getBus(): LateralBus { return this.bus; }
  setNeuronLimit(limit: number): void { this.neuronLimit = limit; }
  getNeuronLimit(): number { return this.neuronLimit; }
  setRegion(region: unknown): void { this.regionRef = region; }

  indexAt(rowIndex: number, colIndex: number): number { return rowIndex * this.width + colIndex; }

  endTick(): void {
    // Per-neuron end-of-tick bookkeeping
    for (let neuronIndex = 0; neuronIndex < this.neurons.length; neuronIndex += 1) {
      const neuronObj = this.neurons[neuronIndex];
      if (typeof (neuronObj as unknown as { resetAccumulatedAmplitude: () => void }).resetAccumulatedAmplitude === 'function') {
        (neuronObj as unknown as { resetAccumulatedAmplitude: () => void }).resetAccumulatedAmplitude();
      }
    }
    // Automatic neuron growth (fallback-streak + cooldown); one growth per layer per tick
    let grownThisTick = false;
    const threshold = this.slotConfig?.fallbackGrowthThreshold ?? 3;
    const cooldownTicks = this.slotConfig?.neuronGrowthCooldownTicks ?? 0;
    const growthEnabled = this.slotConfig?.growthEnabled ?? true;
    const neuronGrowthEnabled = this.slotConfig?.neuronGrowthEnabled ?? true;
    if (growthEnabled && neuronGrowthEnabled) {
      const currentStep = this.bus.getCurrentStep();
      for (let neuronIndex = 0; neuronIndex < this.neurons.length && !grownThisTick; neuronIndex += 1) {
        const neuron = this.neurons[neuronIndex] as unknown as {
          getSlotLimit: () => number;
          getSlotsCount: () => number;
          getLastSlotUsedFallback: () => boolean;
          getFallbackStreak: () => number;
          getLastGrowthTick: () => number;
          setLastGrowthTick: (step: number) => void;
        };
        const limit = neuron.getSlotLimit?.() ?? -1;
        const slotsCount = neuron.getSlotsCount?.() ?? 0;
        const atCapacity = limit >= 0 && slotsCount >= limit;
        const usedFallback = neuron.getLastSlotUsedFallback?.() ?? false;
        const streak = neuron.getFallbackStreak?.() ?? 0;
        const lastGrowth = neuron.getLastGrowthTick?.() ?? -1;
        const cooldownOk = lastGrowth < 0 || (currentStep - lastGrowth) >= cooldownTicks;
        if (atCapacity && usedFallback && streak >= threshold && cooldownOk) {
          const newIndex = this.tryGrowNeuron();
          if (newIndex >= 0) {
            neuron.setLastGrowthTick?.(currentStep);
            grownThisTick = true;
          }
        }
      }
    }
    this.bus.decay();
  }

  tryGrowNeuron(): number {
    if (this.neuronLimit >= 0 && this.neurons.length >= this.neuronLimit) return -1;
    const newIndex = this.neurons.length;
    const neuron = new Neuron(`${this.name}.${newIndex}`, this.bus, this.slotConfig);
    this.neurons.push(neuron);
    try {
      const regionTyped = this.regionRef as { autowireNewNeuronByRef?: (layer: Layer, newIdx: number) => void } | undefined;
      regionTyped?.autowireNewNeuronByRef?.(this, newIndex);
    } catch (error) { void error; }
    return newIndex;
  }

  addNeurons(count: number): void {
    const addCount = Math.max(0, Math.floor(count));
    for (let addIndex = 0; addIndex < addCount; addIndex += 1) {
      const neuronIndex = this.neurons.length;
      const newNeuron = new Neuron(`${this.name}.${neuronIndex}`, this.bus, this.slotConfig);
      this.neurons.push(newNeuron);
    }
  }
}

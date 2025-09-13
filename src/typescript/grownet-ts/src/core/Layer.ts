import { LateralBus } from './LateralBus.js';
import { Neuron } from './Neuron.js';
import { SlotConfig, fixedSlotConfig } from './SlotConfig.js';

export type LayerKind = 'generic' | 'input2d' | 'output2d';

export class Layer {
  private name: string;
  private kind: LayerKind;
  private height: number;
  private width: number;
  private bus: LateralBus;
  private neurons: Array<Neuron> = [];
  private neuronLimit: number;
  private slotConfig: SlotConfig;

  constructor(name: string, kind: LayerKind, height?: number, width?: number, slotConfig?: SlotConfig) {
    this.name = name;
    this.kind = kind;
    this.height = typeof height === 'number' ? height : 0;
    this.width = typeof width === 'number' ? width : 0;
    this.bus = new LateralBus(0.9);
    this.slotConfig = slotConfig || fixedSlotConfig(5.0);
    this.neuronLimit = -1;
    if (kind === 'input2d' || kind === 'output2d') {
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

  indexAt(rowIndex: number, colIndex: number): number { return rowIndex * this.width + colIndex; }

  endTick(): void {
    // In a fuller implementation, per-neuron end-of-tick bookkeeping would live here.
    this.bus.decay();
  }
}


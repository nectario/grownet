import { Layer } from './Layer.js';
import { Neuron } from './Neuron.js';

export class Tract {
  private source: Layer;
  private dest: Layer;
  private feedback: boolean;
  // Optional deterministic mapping for windowed connection: source index -> dest center index
  private centerMap: Map<number, number> | null = null;

  constructor(source: Layer, dest: Layer, feedback: boolean) {
    this.source = source;
    this.dest = dest;
    this.feedback = feedback;
  }

  setCenterMap(centerMap: Map<number, number>): void { this.centerMap = centerMap; }

  getSource(): Layer { return this.source; }
  getDest(): Layer { return this.dest; }

  attachSourceNeuron(newSourceIndex: number): void {
    if (!this.centerMap) return;
    const centerIndex = this.centerMap.get(newSourceIndex);
    if (centerIndex === undefined) return;
    const srcNeurons = this.source.getNeurons();
    const dstNeurons = this.dest.getNeurons();
    if (newSourceIndex < 0 || newSourceIndex >= srcNeurons.length) return;
    const targetNeuron = dstNeurons[centerIndex];
    const srcNeuron: Neuron = srcNeurons[newSourceIndex];
    srcNeuron.connect(targetNeuron, this.feedback);
  }
}


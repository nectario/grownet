import { LateralBus } from './LateralBus.js';
import { SlotConfig } from './SlotConfig.js';
import { Weight } from './Weight.js';

export class Neuron {
  private neuronId: string;
  private slots: Map<number, Weight> = new Map();
  private slotLimit: number;
  private bus: LateralBus;
  private lastInputValue: number = 0.0;
  private firedLast: boolean = false;
  private outgoing: Array<{ target: Neuron; feedback: boolean }> = [];

  private focusAnchor: number = 0.0; // scalar
  private focusSet: boolean = false;

  private anchorRow: number = 0; // 2D
  private anchorCol: number = 0;

  private lastSlotUsedFallback: boolean = false;
  private fallbackStreak: number = 0;
  private lastGrowthTick: number = 0;
  private config: SlotConfig;
  private preferLastSlotOnce: boolean = false;
  private accumulatedAmplitude: number = 0.0;

  constructor(neuronId: string, bus: LateralBus, config: SlotConfig) {
    this.neuronId = neuronId;
    this.bus = bus;
    this.config = config;
    this.slotLimit = config.slotLimit;
  }

  getNeuronId(): string { return this.neuronId; }
  getBus(): LateralBus { return this.bus; }
  getSlotLimit(): number { return this.slotLimit; }
  setSlotLimit(limit: number): void { this.slotLimit = limit; }
  getLastSlotUsedFallback(): boolean { return this.lastSlotUsedFallback; }
  setLastSlotUsedFallback(value: boolean): void { this.lastSlotUsedFallback = value; }
  getFallbackStreak(): number { return this.fallbackStreak; }
  getLastGrowthTick(): number { return this.lastGrowthTick; }
  setLastGrowthTick(step: number): void { this.lastGrowthTick = step; }
  getFiredLast(): boolean { return this.firedLast; }
  getSlotsCount(): number { return this.slots.size; }
  getAccumulatedAmplitude(): number { return this.accumulatedAmplitude; }
  resetAccumulatedAmplitude(): void { this.accumulatedAmplitude = 0.0; }

  onInput(value: number): boolean {
    this.lastInputValue = value;
    if (!this.focusSet) { this.focusAnchor = value; this.focusSet = true; }
    // One-shot preference after unfreeze
    if (this.preferLastSlotOnce && this.lastSelectedKey !== null) {
      const key = this.lastSelectedKey;
      const existing = this.slots.get(key);
      if (existing) {
        this.preferLastSlotOnce = false;
        // reinforce with modulation, then update threshold
        existing.reinforce(this.bus.getModulationFactor());
        this.firedLast = existing.updateThreshold(value * this.bus.getModulationFactor());
        this.lastSlotUsedFallback = false;
        this.accumulatedAmplitude += value;
        return this.firedLast;
      }
    }

    const denom = Math.max(this.config.epsilonScale, Math.abs(this.focusAnchor));
    const distance = Math.abs(value - this.focusAnchor);
    const pct = (distance / denom) * 100.0;
    const binIndex = Math.floor(pct / Math.max(1e-12, this.config.binWidthPercent));
    const slot = this.selectOrCreateSlot(binIndex);
    // reinforce first, then update threshold (parity with other languages)
    slot.reinforce(this.bus.getModulationFactor());
    this.firedLast = slot.updateThreshold(value * this.bus.getModulationFactor());
    if (!this.lastSlotUsedFallback) this.fallbackStreak = 0; // reset when not falling back
    this.accumulatedAmplitude += value;
    return this.firedLast;
  }

  onInput2D(value: number, row: number, col: number): boolean {
    if (!this.focusSet) { this.anchorRow = row; this.anchorCol = col; this.focusSet = true; }
    // One-shot preference after unfreeze
    if (this.preferLastSlotOnce && this.lastSelectedKey !== null) {
      const key = this.lastSelectedKey;
      const existing = this.slots.get(key);
      if (existing) {
        this.preferLastSlotOnce = false;
        existing.reinforce(this.bus.getModulationFactor());
        this.firedLast = existing.updateThreshold(value * this.bus.getModulationFactor());
        this.lastSlotUsedFallback = false;
        this.accumulatedAmplitude += value;
        return this.firedLast;
      }
    }
    // Percent-of-anchor binning per axis
    const eps = Math.max(1e-12, this.config.epsilonScale);
    const denomRow = Math.max(eps, Math.abs(this.anchorRow));
    const denomCol = Math.max(eps, Math.abs(this.anchorCol));
    const rowPct = Math.abs(row - this.anchorRow) / denomRow * 100.0;
    const colPct = Math.abs(col - this.anchorCol) / denomCol * 100.0;
    const rowBin = Math.floor(rowPct / Math.max(1e-12, this.config.rowBinWidthPercent));
    const colBin = Math.floor(colPct / Math.max(1e-12, this.config.colBinWidthPercent));
    const packedKey = rowBin * 1_000_000 + colBin;
    const slot = this.selectOrCreateSlot(packedKey);
    slot.reinforce(this.bus.getModulationFactor());
    this.firedLast = slot.updateThreshold(value * this.bus.getModulationFactor());
    if (!this.lastSlotUsedFallback) this.fallbackStreak = 0;
    this.accumulatedAmplitude += value;
    return this.firedLast;
  }

  onOutput(amplitude: number): void {
    for (const edge of this.outgoing) {
      // Scalar propagation for now; in a more complete system, context would decide 2D vs scalar
      edge.target.onInput(amplitude);
    }
  }

  connect(target: Neuron, feedback: boolean): void {
    this.outgoing.push({ target, feedback });
  }
  getOutgoingCount(): number { return this.outgoing.length; }

  freezeLastSlot(): boolean {
    const lastKey = this.findLastSlotKey();
    if (lastKey === null) return false;
    const weight = this.slots.get(lastKey)!;
    weight.freeze();
    return true;
  }

  unfreezeLastSlot(): boolean {
    const lastKey = this.findLastSlotKey();
    if (lastKey === null) return false;
    const weight = this.slots.get(lastKey)!;
    weight.unfreeze();
    // One-shot reuse next tick
    this.preferLastSlotOnce = true;
    return true;
  }

  private lastSelectedKey: number | null = null;
  private selectOrCreateSlot(key: number): Weight {
    const existing = this.slots.get(key);
    if (existing) { this.lastSlotUsedFallback = false; this.lastSelectedKey = key; return existing; }
    const capacity = this.slotLimit;
    if (capacity >= 0 && this.slots.size >= capacity) {
      // fallback: reuse deterministic existing slot (e.g., smallest key)
      let chosenKey: number | null = null;
      for (const slotKey of this.slots.keys()) { if (chosenKey === null || slotKey < chosenKey) chosenKey = slotKey; }
      if (chosenKey === null) { const weight = new Weight(); this.slots.set(key, weight); this.lastSelectedKey = key; return weight; }
      this.lastSlotUsedFallback = true;
      this.fallbackStreak += 1;
      this.lastSelectedKey = chosenKey;
      return this.slots.get(chosenKey)!;
    }
    const weight = new Weight();
    this.slots.set(key, weight);
    this.lastSlotUsedFallback = false;
    this.lastSelectedKey = key;
    return weight;
  }

  private findLastSlotKey(): number | null {
    if (this.lastSelectedKey !== null) return this.lastSelectedKey;
    let minKey: number | null = null;
    for (const k of this.slots.keys()) { if (minKey === null || k < minKey) minKey = k; }
    return minKey;
  }
}

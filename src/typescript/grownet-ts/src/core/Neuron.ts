import { LateralBus } from './LateralBus.js';
import { SlotConfig } from './SlotConfig.js';
import { Weight } from './Weight.js';

export class Neuron {
  private id: string;
  private slots: Map<number, Weight> = new Map();
  private slotLimit: number;
  private bus: LateralBus;
  private lastInputValue: number = 0.0;
  private firedLast: boolean = false;

  private focusAnchor: number = 0.0; // scalar
  private focusSet: boolean = false;

  private anchorRow: number = 0; // 2D
  private anchorCol: number = 0;

  private lastSlotUsedFallback: boolean = false;
  private fallbackStreak: number = 0;
  private lastGrowthTick: number = 0;
  private config: SlotConfig;

  constructor(id: string, bus: LateralBus, config: SlotConfig) {
    this.id = id;
    this.bus = bus;
    this.config = config;
    this.slotLimit = config.slotLimit;
  }

  getId(): string { return this.id; }
  getBus(): LateralBus { return this.bus; }
  getSlotLimit(): number { return this.slotLimit; }
  setSlotLimit(limit: number): void { this.slotLimit = limit; }
  getLastSlotUsedFallback(): boolean { return this.lastSlotUsedFallback; }
  setLastSlotUsedFallback(value: boolean): void { this.lastSlotUsedFallback = value; }
  getFallbackStreak(): number { return this.fallbackStreak; }
  getLastGrowthTick(): number { return this.lastGrowthTick; }

  onInput(value: number): boolean {
    this.lastInputValue = value;
    if (!this.focusSet) { this.focusAnchor = value; this.focusSet = true; }
    const denom = Math.max(this.config.epsilonScale, Math.abs(this.focusAnchor));
    const distance = Math.abs(value - this.focusAnchor);
    const pct = (distance / denom) * 100.0;
    const binIndex = Math.floor(pct / Math.max(1e-12, this.config.binWidthPercent));
    const slot = this.selectOrCreateSlot(binIndex);
    this.firedLast = slot.updateThreshold(value * this.bus.getModulationFactor());
    return this.firedLast;
  }

  onInput2D(value: number, row: number, col: number): boolean {
    if (!this.focusSet) { this.anchorRow = row; this.anchorCol = col; this.focusSet = true; }
    const rowDistance = Math.abs(row - this.anchorRow);
    const colDistance = Math.abs(col - this.anchorCol);
    const rowPct = rowDistance * this.config.rowBinWidthPercent; // simplification
    const colPct = colDistance * this.config.colBinWidthPercent;
    const rowBin = Math.floor(rowPct / Math.max(1e-12, this.config.rowBinWidthPercent));
    const colBin = Math.floor(colPct / Math.max(1e-12, this.config.colBinWidthPercent));
    const packedKey = rowBin * 1_000_000 + colBin;
    const slot = this.selectOrCreateSlot(packedKey);
    this.firedLast = slot.updateThreshold(value * this.bus.getModulationFactor());
    return this.firedLast;
  }

  freezeLastSlot(): boolean {
    const lastKey = this.findLastSlotKey();
    if (lastKey === null) return false;
    const w = this.slots.get(lastKey)!;
    w.freeze();
    return true;
  }

  unfreezeLastSlot(): boolean {
    const lastKey = this.findLastSlotKey();
    if (lastKey === null) return false;
    const w = this.slots.get(lastKey)!;
    w.unfreeze();
    // Prefer once logic can be modeled externally; here we just unfreeze.
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
      for (const k of this.slots.keys()) { if (chosenKey === null || k < chosenKey) chosenKey = k; }
      if (chosenKey === null) { const w = new Weight(); this.slots.set(key, w); this.lastSelectedKey = key; return w; }
      this.lastSlotUsedFallback = true;
      this.fallbackStreak += 1;
      this.lastSelectedKey = chosenKey;
      return this.slots.get(chosenKey)!;
    }
    const w = new Weight();
    this.slots.set(key, w);
    this.lastSlotUsedFallback = false;
    this.lastSelectedKey = key;
    return w;
  }

  private findLastSlotKey(): number | null {
    if (this.lastSelectedKey !== null) return this.lastSelectedKey;
    let minKey: number | null = null;
    for (const k of this.slots.keys()) { if (minKey === null || k < minKey) minKey = k; }
    return minKey;
  }
}


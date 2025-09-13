export class Weight {
  private strength: number;
  private threshold: number;
  private isFrozen: boolean;

  constructor() {
    this.strength = 0.0;
    this.threshold = 0.0;
    this.isFrozen = false;
  }

  getStrength(): number { return this.strength; }
  getThreshold(): number { return this.threshold; }
  getFrozen(): boolean { return this.isFrozen; }

  reinforce(modulation: number): void {
    if (this.isFrozen) return;
    const step = 0.001 * modulation;
    const next = this.strength + step;
    const clamped = Math.max(-1.0, Math.min(1.0, next));
    this.strength = clamped;
  }

  updateThreshold(effectiveInput: number): boolean {
    // Simple rule: fire if effectiveInput + strength exceeds threshold; then adapt threshold unless frozen
    const fired = (effectiveInput + this.strength) > this.threshold;
    if (!this.isFrozen) {
      const target = fired ? (effectiveInput + this.strength) : this.threshold * 0.99;
      // move threshold slowly toward target
      this.threshold = 0.9 * this.threshold + 0.1 * target;
    }
    return fired;
  }

  freeze(): void { this.isFrozen = true; }
  unfreeze(): void { this.isFrozen = false; }
}


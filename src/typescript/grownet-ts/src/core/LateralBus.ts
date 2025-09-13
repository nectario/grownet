export class LateralBus {
  private inhibitionFactor: number;
  private modulationFactor: number;
  private currentStep: number;
  private inhibitionDecay: number;

  constructor(inhibitionDecay?: number) {
    this.inhibitionFactor = 1.0;
    this.modulationFactor = 1.0;
    this.currentStep = 0;
    this.inhibitionDecay = typeof inhibitionDecay === 'number' ? inhibitionDecay : 0.90;
  }

  getInhibitionFactor(): number { return this.inhibitionFactor; }
  getModulationFactor(): number { return this.modulationFactor; }
  getCurrentStep(): number { return this.currentStep; }

  setModulationFactor(value: number): void { this.modulationFactor = value; }
  setInhibitionFactor(value: number): void { this.inhibitionFactor = value; }

  decay(): void {
    this.inhibitionFactor *= this.inhibitionDecay;
    this.modulationFactor = 1.0;
    this.currentStep += 1;
  }
}


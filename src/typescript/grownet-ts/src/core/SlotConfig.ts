export interface SlotConfig {
  anchorMode: 'FIRST';
  binWidthPercent: number;      // scalar bin width in percent
  epsilonScale: number;         // floor for denominator when anchor ~ 0
  spatialEnabled: boolean;
  rowBinWidthPercent: number;
  colBinWidthPercent: number;
  slotLimit: number;            // -1 = unlimited
  growthEnabled: boolean;
  neuronGrowthEnabled: boolean;
  layerGrowthEnabled: boolean;
  fallbackGrowthThreshold: number;
  neuronGrowthCooldownTicks: number;
  layerNeuronLimitDefault: number;
}

export function fixedSlotConfig(deltaPercent: number): SlotConfig {
  return {
    anchorMode: 'FIRST',
    binWidthPercent: deltaPercent,
    epsilonScale: 1e-9,
    spatialEnabled: false,
    rowBinWidthPercent: deltaPercent,
    colBinWidthPercent: deltaPercent,
    slotLimit: -1,
    growthEnabled: true,
    neuronGrowthEnabled: true,
    layerGrowthEnabled: true,
    fallbackGrowthThreshold: 3,
    neuronGrowthCooldownTicks: 100,
    layerNeuronLimitDefault: 1024,
  };
}


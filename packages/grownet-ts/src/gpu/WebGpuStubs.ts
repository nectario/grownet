export interface DeviceInfo {
  available: boolean;
  backend: 'cpu' | 'gpu';
}

export function tryAcquireDevice(): DeviceInfo {
  // Stubbed: Node WebGPU may not be available. Always report CPU fallback.
  return { available: false, backend: 'cpu' };
}


import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('Mesh autowire replay', () => {
  it('Newly grown neuron in source layer wires to destination via mesh rules', () => {
    const region = new Region('mesh-autowire');
    const layerA = region.addLayer(2); // two neurons
    const layerB = region.addLayer(3); // three neurons
    // Connect with p=1.0 to record a mesh rule
    const edges = region.connectLayers(layerA, layerB, 1.0, false);
    expect(edges).toBeGreaterThanOrEqual(2 * 3);

    // Grow one neuron in layerA
    const layerARef = (region as unknown as { layers: Array<any> }).layers[layerA];
    const newIndex = layerARef.tryGrowNeuron();
    expect(newIndex).toBeGreaterThanOrEqual(0);

    // Check that the new neuron has at least as many outgoing as B's size (p=1.0)
    const neuronsA = layerARef.getNeurons();
    const newNeuron = neuronsA[newIndex];
    const outCount = (newNeuron as unknown as { getOutgoingCount: () => number }).getOutgoingCount();
    expect(outCount).toBeGreaterThanOrEqual(3);
  });
});


import { describe, it, expect } from 'vitest';
import { Region } from '../src/Region.js';

describe('Windowed wiring unique sources count', () => {
  it('4x4, VALID, kernel 4x4 -> 16 uniques', () => {
    const region = new Region('win-smoke');
    const inputLayerId = region.addInputLayer2D(4, 4, 1.0, 0.01);
    const outputLayerId = region.addOutputLayer2D(4, 4, 0.0);
    const uniqueSources = region.connectLayersWindowed(
      inputLayerId, outputLayerId, 4, 4, 1, 1, 'valid', false,
    );
    expect(uniqueSources).toBe(16);
  });

  it('4x4, VALID, kernel 2x2, stride 2 -> 16 uniques', () => {
    const region = new Region('win-smoke');
    const inputLayerId = region.addInputLayer2D(4, 4, 1.0, 0.01);
    const outputLayerId = region.addOutputLayer2D(4, 4, 0.0);
    const uniqueSources = region.connectLayersWindowed(
      inputLayerId, outputLayerId, 2, 2, 2, 2, 'valid', false,
    );
    expect(uniqueSources).toBe(16);
  });

  it('5x5, VALID, kernel 3x3, stride 3 -> 9 uniques', () => {
    const region = new Region('win-smoke');
    const inputLayerId = region.addInputLayer2D(5, 5, 1.0, 0.01);
    const outputLayerId = region.addOutputLayer2D(5, 5, 0.0);
    const uniqueSources = region.connectLayersWindowed(
      inputLayerId, outputLayerId, 3, 3, 3, 3, 'valid', false,
    );
    expect(uniqueSources).toBe(9);
  });

  it('5x5, SAME, kernel 3x3, stride 3 -> 25 uniques', () => {
    const region = new Region('win-smoke');
    const inputLayerId = region.addInputLayer2D(5, 5, 1.0, 0.01);
    const outputLayerId = region.addOutputLayer2D(5, 5, 0.0);
    const uniqueSources = region.connectLayersWindowed(
      inputLayerId, outputLayerId, 3, 3, 3, 3, 'same', false,
    );
    expect(uniqueSources).toBe(25);
  });
});


import { broadcastFrame } from '../ws.js';

interface SimState {
  width: number;
  height: number;
  row: number;
  col: number;
  dr: number;
  dc: number;
}

let timer: ReturnType<typeof setInterval> | null = null;

export function startSim(width?: number, height?: number): void {
  if (timer) return;
  const state: SimState = { width: width || 64, height: height || 64, row: 0, col: 0, dr: 1, dc: 1 };
  timer = setInterval(() => {
    // update bouncing dot
    state.row += state.dr; state.col += state.dc;
    if (state.row <= 0 || state.row >= state.height - 1) state.dr *= -1;
    if (state.col <= 0 || state.col >= state.width - 1) state.dc *= -1;
    const active = [[state.row, state.col]];
    broadcastFrame({ grid: { width: state.width, height: state.height }, active });
  }, 16);
}

export function stopSim(): void {
  if (timer) clearInterval(timer);
  timer = null;
}


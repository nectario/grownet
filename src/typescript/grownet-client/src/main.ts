const canvas = document.getElementById('cv') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const wsStatus = document.getElementById('ws') as HTMLSpanElement;
const fpsLabel = document.getElementById('fps') as HTMLSpanElement;

interface FrameMessage { type: 'frame'; data: { grid: { width: number; height: number }; active: Array<[number, number]> }; timestamp: number }

let gridWidth = 64;
let gridHeight = 64;
let activeCells: Array<[number, number]> = [];

function draw() {
  const w = canvas.width; const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#0a0a0a';
  ctx.fillRect(0, 0, w, h);
  const cellSize = Math.min(w / gridWidth, h / gridHeight);
  ctx.fillStyle = '#22cc88';
  for (let i = 0; i < activeCells.length; i += 1) {
    const [r, c] = activeCells[i];
    ctx.fillRect(Math.floor(c * cellSize), Math.floor(r * cellSize), Math.ceil(cellSize), Math.ceil(cellSize));
  }
}

let lastTime = performance.now();
let frames = 0;
function animate() {
  requestAnimationFrame(animate);
  draw();
  frames += 1;
  const now = performance.now();
  if (now - lastTime > 1000) {
    fpsLabel.textContent = String(frames);
    frames = 0; lastTime = now;
  }
}

function connect() {
  const endpoint = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host.replace(/:\d+$/, ':3333') + '/ws';
  const ws = new WebSocket(endpoint);
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => { wsStatus.textContent = 'connected'; };
  ws.onclose = () => { wsStatus.textContent = 'disconnected'; setTimeout(connect, 1000); };
  ws.onerror = () => { wsStatus.textContent = 'error'; };
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data) as FrameMessage;
      if (msg.type === 'frame') {
        gridWidth = msg.data.grid.width;
        gridHeight = msg.data.grid.height;
        activeCells = msg.data.active;
      }
    } catch (_e) { /* ignore */ }
  };
}

connect();
animate();


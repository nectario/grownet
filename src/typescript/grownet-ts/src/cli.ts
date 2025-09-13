import { createServer } from './server/Server.js';
import { startSim } from './server/sim/SimLoop.js';

async function main() {
  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3333;
  const host = process.env.HOST || '0.0.0.0';
  const app = await createServer();
  await app.listen({ port, host });
  if (process.env.GROWNET_SIM === '1') startSim();
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});

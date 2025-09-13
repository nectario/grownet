Absolutely—here’s the **“No‑Aliases” revision** of the TypeScript port PR. I removed **all forms of aliasing** (type aliases, import/export renames, namespace aliases, and tsconfig path aliases) and tightened linting so they can’t creep back in. This keeps everything else from your original plan intact (PAL v2 determinism, Region APIs, server endpoints, GPU stubs), just without aliases. 

------

# PR: Port GrowNet Server to TypeScript/JavaScript (Phase 1) — **No‑Aliases Edition**

> Ports GrowNet’s server runtime to TypeScript with contract parity to Python/Mojo, **without any aliases**. Implements PAL v2 determinism, public `Region` APIs, and minimal GPU stubs. Exposes HTTP endpoints for core ops; ships as an npm package and a deployable service. 

## What changed vs. the prior draft

- **No TypeScript aliases**
  - No `type X = ...` declarations (use `interface` for objects; unions are written inline at call‑sites).
  - No `namespace` wrappers (plain ESM modules with named exports).
- **No import/export aliasing**
  - No `import * as X`, no `import { Foo as Bar }`, no `export { Foo as Bar }`, no `export * as Foo`.
  - Only **named imports/exports** where exported and local names are identical.
- **No tsconfig path aliases**
  - Only relative ESM imports (`../..`), no `"paths"` mapping.
- **Linting hard‑stops alias usage**
  - ESLint bans `TSTypeAliasDeclaration`, `ImportNamespaceSpecifier`, `ImportSpecifier`/`ExportSpecifier` renames, and `ExportAllDeclaration` with a binding.

Everything else (PAL v2 semantics, APIs, server, tests, CI) follows your original plan. 

------

## Goals (unchanged)

- Type‑safe, deterministic server runtime on Node 18/20.
- Public API parity: `Region.computeSpatialMetrics` + `tickND`.
- PAL v2 in TS: `parallelFor` / `parallelMap`, deterministic ordered reduction, env overrides.
- **Style:** PascalCase classes, camelCase methods, **no snake_case**, avoid 1–2 char identifiers (loop indices `i/j/k` OK).
   *Plus:* **no aliases** anywhere. 

## Non‑Goals (this PR)

- UI client.
- Full GPU compute (CPU‑first; WebGPU stubbed).
- Rewriting C++/Java; used only for parity checks. 

------

## Package Layout

```
src/typescript/
  grownet-ts/
    src/
      index.ts                  # explicit named exports, no barrels-with-renames
      Region.ts
      metrics/RegionMetrics.ts
      pal/index.ts              # PAL v2 (no namespace), worker pool w/ ordered reduction
      pal/worker/Pool.ts        # bounded worker_threads pool (no alias names)
      wiring/TopographicWiring.ts
      server/Server.ts          # Fastify server
      server/routes/computeSpatialMetrics.ts
      server/routes/tickNd.ts
      gpu/WebGpuStubs.ts        # optional; CPU fallback always available
    tests/
      PalDeterminism.test.ts
      SpatialMetricsPublic.test.ts
      NdTickSmoke.test.ts
    package.json
    tsconfig.json               # no "paths"
    README.md
tsconfig.base.json              # no "paths"
.eslintrc.cjs                   # blocks aliases
.prettierrc
```

------

## Public API (TypeScript, **no aliases**)

```ts
// src/typescript/grownet-ts/src/pal/index.ts
export interface ParallelOptions {
  maxWorkers?: number;
  tileSize?: number;
  device?: 'cpu' | 'gpu' | 'auto';
  vectorizationEnabled?: boolean;
  reduction?: 'ordered' | 'pairwiseTree';
}

export interface IndexDomain {
  size(): number;
  at(index: number): number;
}

export function configure(options: ParallelOptions): void;

export function parallelFor<T>(
  domain: { size(): number; at(i: number): T },
  kernel: (item: T) => void,
  options?: ParallelOptions
): Promise<void> | void;

export function parallelMap<T, R>(
  domain: { size(): number; at(i: number): T },
  kernel: (item: T) => R,
  reduceInOrder: (values: R[]) => R,
  options?: ParallelOptions
): Promise<R> | R;

export function counterRng(
  seed: number | bigint,
  step: number | bigint,
  drawKind: number,
  layerIndex: number,
  unitIndex: number,
  drawIndex: number
): number;
// src/typescript/grownet-ts/src/Region.ts
import { ParallelOptions } from './pal/index.js';
import { RegionMetrics } from './metrics/RegionMetrics.js';

export class Region {
  constructor(name: string);

  computeSpatialMetrics(
    image2d:
      | number[][]
      | Float64Array
      | { data: Float64Array; height: number; width: number },
    preferOutput: boolean
  ): RegionMetrics;

  tickND(
    port: string,
    tensor: number[] | number[][] | number[][][],
    options?: ParallelOptions
  ): RegionMetrics;
}
// src/typescript/grownet-ts/src/metrics/RegionMetrics.ts
export class RegionMetrics {
  constructor(
    deliveredEvents: number,
    totalSlots: number,
    totalSynapses: number,
    activePixels: number,
    centroidRow: number,
    centroidCol: number,
    bboxRowMin: number,
    bboxRowMax: number,
    bboxColMin: number,
    bboxColMax: number
  );

  getDeliveredEvents(): number;
  getTotalSlots(): number;
  getTotalSynapses(): number;
  getActivePixels(): number;
  getCentroidRow(): number;
  getCentroidCol(): number;
  getBboxRowMin(): number;
  getBboxRowMax(): number;
  getBboxColMin(): number;
  getBboxColMax(): number;
}
```

> Note: no `namespace`, no `type` declarations, no `import ... as ...`, and no import/export renames. This preserves your API plan while satisfying **No Aliases**. 

------

## PAL v2 (deterministic), without aliases

- **Workers:** `worker_threads` with a bounded pool. Submission order → bucket per worker → **ordered reduction** for determinism.
- **Options:** `maxWorkers` default `os.cpus().length` (or env `GROWNET_PAL_MAX_WORKERS`), `tileSize` for canonical tiling, `reduction: 'ordered'`.
- **Device:** `'cpu' | 'gpu' | 'auto'`; GPU is *feature‑detected* (WebGPU stub), otherwise CPU. No behavior change if GPU is unavailable.
- **RNG:** SplitMix64‑style `counterRng` identical to C++/Python/Mojo.
- **Sync/Async:** If `maxWorkers <= 1`, functions run synchronously; else they return `Promise`. 

------

## Server (HTTP)

- **Fastify**, base path `/api/v1`:
  - POST `/region/compute-spatial-metrics`
  - POST `/region/tick-nd`
- **Validation:** Ajv schemas (strict). **No alias imports** inside server code.
- **Diagnostics:** pino logging, request ids, latency metrics. 

------

## Determinism & Tests (unchanged)

- **Determinism:** identical `counterRng` constants; **ordered** reduction; stable iteration.
- **Tests:** `PalDeterminism.test.ts`, `SpatialMetricsPublic.test.ts`, `NdTickSmoke.test.ts`. 

------

## Lint, Style & CI (now blocking aliases)

**.eslintrc.cjs**

```js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier',
  ],
  rules: {
    // Style you already asked for
    '@typescript-eslint/naming-convention': [
      'error',
      { selector: 'class', format: ['PascalCase'] },
      { selector: 'function', format: ['camelCase'] },
      { selector: 'method', format: ['camelCase'] },
      { selector: 'variable', format: ['camelCase', 'UPPER_CASE'] },
      { selector: 'property', format: ['camelCase', 'UPPER_CASE'] }
    ],
    'id-length': ['error', { min: 3, exceptions: ['i', 'j', 'k'] }],

    // **No Aliases** — hard bans
    // 1) Disallow all TypeScript type aliases
    'no-restricted-syntax': [
      'error',
      { selector: 'TSTypeAliasDeclaration', message: 'Do not use type aliases.' },
      { selector: 'ImportNamespaceSpecifier', message: 'Do not use namespace import aliases.' },
      { selector: 'ImportSpecifier[imported.name!=local.name]', message: 'Do not alias imported names.' },
      { selector: 'ExportSpecifier[exported.name!=local.name]', message: 'Do not alias exported names.' },
      { selector: 'ExportAllDeclaration[exported!=null]', message: 'Do not alias re-exported module members.' },
      { selector: 'TSImportEqualsDeclaration', message: 'Do not use import equals (alias).' }
    ],

    // Prefer interfaces for object shapes
    '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],

    // Optional: prefer named exports
    'import/prefer-default-export': 'off',
    'import/no-default-export': 'warn'
  }
};
```

**tsconfig.json**

```json
{
  "extends": "../../../tsconfig.base.json",
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "moduleResolution": "Node",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "noEmit": false,
    "outDir": "dist"
    /* No "paths": no path aliases */
  },
  "include": ["src"]
}
```

**CI**
 Add `eslint` and `tsc --noEmit` steps; CI fails if any alias slips in.

------

## GPU Path (stub, no aliases)

- Feature‑detect Node WebGPU (Dawn). If absent or unsupported, **fallback to CPU**.
- Minimal kernels for demos (identity/addScalar/scale) and always deterministic; no “as” exports, no namespace imports. 

------

## Implementation Checklist (updated)

1. Scaffold `src/typescript/grownet-ts` with **ESM** and **strict** tsconfig (no paths).
2. Implement PAL v2 in `src/pal` using **worker_threads** pool (bounded) with **ordered reduction**.
3. Implement `RegionMetrics` and `Region.computeSpatialMetrics` + `tickND`.
4. Add Fastify server with the two routes + schemas.
5. Write tests (determinism, metrics, ND tick).
6. Wire GitHub Actions: lint → typecheck → test → build.
7. Document usage in README + minimal OpenAPI JSON.

------

## Acceptance Criteria (unchanged)

- `computeSpatialMetrics` parity with Python on canonical frames.
- PAL determinism holds at different worker counts.
- **Lint blocks aliases;** type‑check/build/tests green on Linux/Windows. 

------

### Why this satisfies “No Aliases”

- **Language level:** No `type` declarations; only `interface`/`class`/inline unions. No `namespace`.
- **Module level:** No `import * as`, no `as` renames in import or export positions; no `export * as`.
- **Tooling:** No tsconfig `paths`. ESLint forbids alias constructs at AST level, so reviews don’t need to catch them manually.


#!/usr/bin/env bash
set -uo pipefail

python_exec="${PYTHON:-python}"
contract_version="${GROWNET_CONTRACT_VERSION:-5}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

pass_bus_decay=false
pass_windowed=false
pass_one_growth=false

bus_decay_cmd=(bash -lc "cd \"${repo_root}\" && npm -s --workspace @grownet/server-ts run test -- tests/LateralBusAndWeight.test.ts")
windowed_cmd=(bash -lc "cd \"${repo_root}\" && npm -s --workspace @grownet/server-ts run test -- tests/WiringWindowedSmoke.test.ts")
one_growth_cmd=(bash -lc "cd \"${repo_root}\" && npm -s --workspace @grownet/server-ts run test -- tests/RegionLayerGrowthPolicy.test.ts")

if "${bus_decay_cmd[@]}" >/dev/null 2>&1; then pass_bus_decay=true; fi
if "${windowed_cmd[@]}" >/dev/null 2>&1; then pass_windowed=true; fi
if "${one_growth_cmd[@]}" >/dev/null 2>&1; then pass_one_growth=true; fi

overall_pass=false
if [[ "${pass_bus_decay}" == "true" && "${pass_windowed}" == "true" && "${pass_one_growth}" == "true" ]]; then
  overall_pass=true
fi

PASS_BUS_DECAY="${pass_bus_decay}" \
PASS_WINDOWED_WIRING="${pass_windowed}" \
PASS_ONE_GROWTH="${pass_one_growth}" \
OVERALL_PASS="${overall_pass}" \
"${python_exec}" - <<'PY'
import json
import os


def to_bool(value: str) -> bool:
    return str(value).lower() == "true"


print(
    json.dumps(
        {
            "language": "typescript",
            "contractVersion": int(os.environ.get("GROWNET_CONTRACT_VERSION", "5")),
            "tests": {
                "bus_decay_parity": {"pass": to_bool(os.environ.get("PASS_BUS_DECAY", "false"))},
                "windowed_wiring_return_semantics": {"pass": to_bool(os.environ.get("PASS_WINDOWED_WIRING", "false"))},
                "one_growth_per_region_per_tick": {"pass": to_bool(os.environ.get("PASS_ONE_GROWTH", "false"))},
            },
            "pass": to_bool(os.environ.get("OVERALL_PASS", "false")),
        }
    )
)
PY

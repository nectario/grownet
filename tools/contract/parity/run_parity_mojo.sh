#!/usr/bin/env bash
set -uo pipefail

python_exec="${PYTHON:-python}"
contract_version="${GROWNET_CONTRACT_VERSION:-5}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

pass_bus_decay=false
pass_windowed=false
pass_one_growth=false
skipped=false
skip_reason=""

if ! command -v mojo >/dev/null 2>&1; then
  skipped=true
  skip_reason="mojo tool not found"
else
  if mojo run "${repo_root}/src/mojo/tests/bus_decay.mojo" >/dev/null 2>&1; then pass_bus_decay=true; fi
  if mojo run "${repo_root}/src/mojo/tests/windowed_tracts.mojo" >/dev/null 2>&1; then pass_windowed=true; fi
  if mojo run "${repo_root}/src/mojo/tests/one_growth_per_tick.mojo" >/dev/null 2>&1; then pass_one_growth=true; fi
fi

overall_pass=false
if [[ "${skipped}" == "true" ]]; then
  overall_pass=true
else
  if [[ "${pass_bus_decay}" == "true" && "${pass_windowed}" == "true" && "${pass_one_growth}" == "true" ]]; then
    overall_pass=true
  fi
fi

PASS_BUS_DECAY="${pass_bus_decay}" \
PASS_WINDOWED_WIRING="${pass_windowed}" \
PASS_ONE_GROWTH="${pass_one_growth}" \
OVERALL_PASS="${overall_pass}" \
SKIPPED="${skipped}" \
SKIP_REASON="${skip_reason}" \
"${python_exec}" - <<'PY'
import json
import os


def to_bool(value: str) -> bool:
    return str(value).lower() == "true"


print(
    json.dumps(
        {
            "language": "mojo",
            "contractVersion": int(os.environ.get("GROWNET_CONTRACT_VERSION", "5")),
            "tests": {
                "bus_decay_parity": {"pass": to_bool(os.environ.get("PASS_BUS_DECAY", "false"))},
                "windowed_wiring_return_semantics": {"pass": to_bool(os.environ.get("PASS_WINDOWED_WIRING", "false"))},
                "one_growth_per_region_per_tick": {"pass": to_bool(os.environ.get("PASS_ONE_GROWTH", "false"))},
            },
            "pass": to_bool(os.environ.get("OVERALL_PASS", "false")),
            "skipped": to_bool(os.environ.get("SKIPPED", "false")),
            "skipReason": os.environ.get("SKIP_REASON") or None,
        }
    )
)
PY

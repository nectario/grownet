#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python_exec="${PYTHON:-python}"

echo "[contract] validate contract schema"
"${python_exec}" tools/contract/validate_contract.py --require-evaluation-ku-bku

echo "[contract] check canonical contract"
"${python_exec}" tools/contract/check_contract_canonical.py --show-diff

echo "[contract] validate docs/READ_ORDER.md refs"
"${python_exec}" tools/contract/check_read_order_refs.py

echo "[contract] API presence scan (signature presence only)"
"${python_exec}" tools/contract/parity/check_api_presence.py

echo "[contract] parity smoke (best-effort)"
"${python_exec}" tools/contract/parity/aggregate_results.py

echo "[contract] done"


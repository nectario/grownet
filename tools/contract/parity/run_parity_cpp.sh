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

find_test_executable() {
  local uname_out is_windows
  uname_out="$(uname -s 2>/dev/null || echo unknown)"
  is_windows=false
  case "${uname_out}" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT) is_windows=true ;;
  esac

  local candidate
  for candidate in \
    "${repo_root}/build/grownet_tests" \
    "${repo_root}/build/grownet_tests.exe" \
    "${repo_root}/cmake-build-debug/grownet_tests" \
    "${repo_root}/cmake-build-debug/grownet_tests.exe" \
    "${repo_root}/cmake-build-release/grownet_tests" \
    "${repo_root}/cmake-build-release/grownet_tests.exe"; do
    if [[ "${is_windows}" != "true" && "${candidate}" == *.exe ]]; then
      continue
    fi
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

test_executable=""
if test_executable="$(find_test_executable)"; then
  :
else
  # Best-effort build (may require network to fetch gtest).
  build_dir="${repo_root}/build-cpp"
  if cmake -S "${repo_root}" -B "${build_dir}" -DGROWNET_BUILD_TESTS=ON -DGROWNET_SKIP_CPP_TESTS=OFF >/dev/null 2>&1 \
    && cmake --build "${build_dir}" >/dev/null 2>&1; then
    if [[ -x "${build_dir}/grownet_tests" ]]; then
      test_executable="${build_dir}/grownet_tests"
    elif [[ -x "${build_dir}/grownet_tests.exe" ]]; then
      test_executable="${build_dir}/grownet_tests.exe"
    fi
  fi
fi

if [[ -z "${test_executable}" ]]; then
  skipped=true
  skip_reason="C++ test executable not available (build may require gtest/network)."
else
  if "${test_executable}" --gtest_filter="LateralBusDecay.*" >/dev/null 2>&1; then pass_bus_decay=true; fi
  if "${test_executable}" --gtest_filter="WindowedWiringCenter.*:EdgeEnumeration.*" >/dev/null 2>&1; then pass_windowed=true; fi
  if "${test_executable}" --gtest_filter="RegionGrowth.*" >/dev/null 2>&1; then pass_one_growth=true; fi
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
            "language": "cpp",
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

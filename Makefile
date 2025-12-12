.PHONY: test codex-web local ci contract contract-validate contract-canonicalize contract-check contract-doc-refs contract-api-presence contract-parity

codex-web:
	@bash scripts/run_tests_codex_web.sh

# Full local run (requires tools & network):
local:
	@echo "Python"; PYTHONPATH=src/python pytest -q src/python/tests
	@echo "Java"; mvn -q test
	@echo "C++"; cmake -S . -B build && cmake --build build && ctest --test-dir build -V
	@echo "Mojo"; bash scripts/run_mojo_tests.sh || true

# CI orchestration hint (adjust in your pipeline):
ci: local

contract:
	@bash tools/contract/run_all_checks.sh

contract-validate:
	@python tools/contract/validate_contract.py --require-evaluation-ku-bku

contract-canonicalize:
	@python tools/contract/canonicalize_contract.py

contract-check:
	@python tools/contract/check_contract_canonical.py --show-diff

contract-doc-refs:
	@python tools/contract/check_read_order_refs.py

contract-api-presence:
	@python tools/contract/parity/check_api_presence.py

contract-parity:
	@python tools/contract/parity/aggregate_results.py

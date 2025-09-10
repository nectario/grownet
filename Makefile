.PHONY: test codex-web local ci

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


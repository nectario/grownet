import sys
import os
from pathlib import Path

# Ensure both the repo root and src/python are importable for tests that use
# either `from region import Region` or `from src.python...` imports.

# repo root = .../GrowNet
ROOT = Path(__file__).resolve().parents[3]
PY_SRC = ROOT / "src" / "python"

for p in (str(ROOT), str(PY_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ---- compat fixture for deliveredEvents counting ----
import os
import pytest

@pytest.fixture
def compat_bound_delivered_count():
    """Temporarily count deliveredEvents as number of bound layers."""
    old = os.environ.get("GROWNET_COMPAT_DELIVERED_COUNT")
    os.environ["GROWNET_COMPAT_DELIVERED_COUNT"] = "bound"
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("GROWNET_COMPAT_DELIVERED_COUNT", None)
        else:
            os.environ["GROWNET_COMPAT_DELIVERED_COUNT"] = old

# Pure‑Python mirror of the Mojo API (no leading underscores)

from collections import defaultdict
from math import fabs
import yaml, importlib.resources as pkg

# ------------------------------------------------------------------
# Load YAML defaults so Python & Mojo share a single source of truth
CFG = yaml.safe_load(open("experiments/E00_omniglot.yaml"))

EPS         = CFG["eps"]
BETA        = CFG["beta"]
ETA         = CFG["eta"]
R_STAR      = CFG["r_star"]
HIT_SAT     = CFG["hit_saturation"]
SLOT_LIMIT  = CFG["max_slots_per_neuron"]

# ------------------------------------------------------------------
# Helper functions (from math_utils.mojo)

def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)

def smooth_clamp(x, lo, hi):
    return smoothstep(0.0, 1.0, (x - lo) / (hi - lo)) * (hi - lo) + lo

def round_two(x):
    return 0.0 if x == 0 else round(x * 10) / 10.0


# ------------------------------------------------------------------
class Weight:
    def __init__(self, parent, child, step_val=0.001):
        self.parent, self.child = parent, child
        self.step_val   = step_val
        self.strength   = 0.0
        self.hits       = 0

    def reinforce(self):
        if self.hits < HIT_SAT:
            self.strength = smooth_clamp(self.strength + self.step_val, -1.0, 1.0)
            self.hits += 1


class MemoryCell:
    def __init__(self):
        self.last_raw = 0.0
        self.slots    = {}

    def pct_delta(self, new_val):
        return 0.0 if self.last_raw == 0 else (new_val - self.last_raw) / self.last_raw


class Neuron:
    def __init__(self, nid="root"):
        self.id          = nid
        self.cell        = MemoryCell()
        self.outbound    = {}
        # adaptive‑threshold state
        self.theta       = 0.0
        self.ema_rate    = 0.0
        self.seen_one    = False

    # --------------- public API -----------------
    def onInput(self, x: float):
        """Main entry point—mirrors Mojo signature."""

        # ---- T0 imprint
        if not self.seen_one:
            self.theta    = fabs(x) * (1.0 + EPS)
            self.seen_one = True

        # ---- slot key & creation
        delta   = round_two(self.cell.pct_delta(x))
        bin_id  = int(delta * 10)        # e.g. 0.23 → 2
        weight  = self.cell.slots.get(bin_id)
        if weight is None:
            weight = self.spawnSlot(bin_id)

        # ---- reinforce & fire
        weight.reinforce()
        fired = False
        if weight.strength > self.theta:
            fired = True
            weight.child.onInput(x)

        # ---- T2 homeostasis
        self.ema_rate = (1 - BETA) * self.ema_rate + BETA * (1.0 if fired else 0.0)
        self.theta   += ETA * (self.ema_rate - R_STAR)

        self.cell.last_raw = x

    # --------------- helpers --------------------
    def spawnSlot(self, bin_id: int) -> Weight:
        if SLOT_LIMIT is not None and len(self.cell.slots) >= SLOT_LIMIT:
            return self.reuseSlot(bin_id)

        child  = Neuron(f"{self.id}-{bin_id}")
        weight = Weight(parent=self, child=child)
        self.cell.slots[bin_id] = weight
        self.outbound[child.id] = weight
        return weight

    def reuseSlot(self, bin_id: int) -> Weight:
        # trivial policy: reuse the first slot
        k = next(iter(self.cell.slots))
        return self.cell.slots[k]

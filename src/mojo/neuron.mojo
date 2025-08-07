# neuron.mojo  – top of file
import math_utils
# Dict is in prelude since v25.5; no explicit import needed


# ---------- Weight -----------------------------------------------------------
struct Weight:
    id:        String
    parent:    @owned Neuron*
    child:     @owned Neuron*
    step_val:  F64   = 0.001        # α (reinforcement increment)
    strength:  F64   = 0.0          # −1 … +1
    hits:      Int   = 0            # reinforcement count

    const HIT_SATURATION: Int = get_hit_sat()  # injected from YAML

    fn reinforce(self):
        if self.hits < self.HIT_SATURATION:
            self.strength = mu.smooth_clamp(self.strength + self.step_val, -1.0, 1.0)
            self.hits    += 1

# ---------- MemoryCell -------------------------------------------------------
struct MemoryCell:
    last_raw: F64 = 0.0
    slots:    Dict[Int, @owned Weight*]

    fn pct_delta(self, new_val: F64) -> F64:
        if self.last_raw == 0.0: return 0.0
        return (new_val - self.last_raw) / self.last_raw

# ---------- Neuron -----------------------------------------------------------
struct Neuron:
    id: String

    cell: MemoryCell
    outbound: Dict[String, @owned Weight*]

    # --- adaptive‑threshold state ---
    theta:    F64 = 0.0        # current threshold
    ema_rate: F64 = 0.0        # r̂
    seen_one: Bool = False     # T0 done?
    # --- hyper‑params (injected from YAML) ---
    const EPS:    F64 = get_eps()
    const BETA:   F64 = get_beta()
    const ETA:    F64 = get_eta()
    const R_STAR: F64 = get_r_star()
    const MAX_SLOTS: Int? = get_max_slots()

    # ...
fn on_input(self, x: F64):
    # T0 imprint -----------------------------------------
    if not self.seen_one:
        self.theta = abs(x) * (1.0 + self.EPS)
        self.seen_one = True

    # slot key & creation --------------------------------
    let Δ      = math_utils.round_two(self.cell.pct_delta(x))
    let bin_id = Int(Δ * 10.0)
    let w      = self.cell.slots.get_or_insert_with(
        bin_id, lambda _: self.spawnSlot(bin_id))

    # reinforce & fire -----------------------------------
    w.reinforce()
    var fired = 0
    if w.strength > self.theta:
        fired = 1
        w.child.on_input(x)

    # homeostasis ----------------------------------------
    self.ema_rate = (1.0 - self.BETA) * self.ema_rate + self.BETA * F64(fired)
    self.theta   += self.ETA * (self.ema_rate - self.R_STAR)
    self.cell.last_raw = x

# ---------- helpers (renamed, no leading _) -------------
fn spawnSlot(self, bin_id: Int) -> @owned Weight*:
    if (self.MAX_SLOTS is Int) and (self.cell.slots.len >= self.MAX_SLOTS):
        return self.reuseSlot(bin_id)
    let child = @owned Neuron(id=f"{self.id}-{bin_id}")
    let w     = @owned Weight(id=f"w{bin_id}", parent=@borrow self, child=child)
    self.outbound[child.id] = w
    return w

fn reuseSlot(self, bin_id: Int) -> @owned Weight*:
    return self.cell.slots.values()[0]


# ---------- YAML hooks (populated at runtime) ----------
# These dummy definitions are overwritten by train_loop.mojo
fn get_eps()  -> F64  : return 0.02
fn get_beta() -> F64  : return 0.01
fn get_eta()  -> F64  : return 0.02
fn get_r_star()-> F64  : return 0.05
fn get_max_slots() -> Int? : return None
fn get_hit_sat() -> Int : return 10_000

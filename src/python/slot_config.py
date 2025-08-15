class SlotPolicy:
    FIXED = "fixed"
    NONUNIFORM = "nonuniform"
    ADAPTIVE = "adaptive"

class SlotConfig:
    def __init__(self, policy=SlotPolicy.FIXED, fixed_delta_percent=10.0, custom_edges=None):
        self.policy = policy
        self.fixed_delta_percent = float(fixed_delta_percent)
        self.custom_edges = list(custom_edges) if custom_edges else []

def fixed(delta_percent=10.0):
    return SlotConfig(SlotPolicy.FIXED, fixed_delta_percent=delta_percent)

def nonuniform(edges_percent):
    return SlotConfig(SlotPolicy.NONUNIFORM, custom_edges=list(edges_percent))

def adaptive():
    # placeholder; policy hook for future work
    return SlotConfig(SlotPolicy.ADAPTIVE)

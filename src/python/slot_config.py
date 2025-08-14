from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

class SlotPolicy:
    FIXED = "fixed"
    NONUNIFORM = "nonuniform"
    ADAPTIVE = "adaptive"

@dataclass
class SlotConfig:
    policy: str = SlotPolicy.FIXED
    slot_width_percent: float = 10.0                 # used by FIXED/ADAPTIVE
    nonuniform_edges: List[float] = field(default_factory=list)  # ascending percent edges
    max_slots: Optional[int] = None                  # None => unbounded

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInterfaceOptions:
    threshold: float = 0.5
    set_lower_bound: bool = True
    set_upper_bound: bool = True
    snap_value: Optional[float] = 1.0

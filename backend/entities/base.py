from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BaseEntity:
    id: Optional[int] = None

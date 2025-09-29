from dataclasses import dataclass
from .base import BaseEntity
from backend.exceptions import EmptyMinisterNameError


@dataclass(frozen=True)
class Minister(BaseEntity):
    name: str = ""

    """Represents a government minister."""

    def __post_init__(self):
        if not self.name:
            raise EmptyMinisterNameError()

    def __repr__(self) -> str:
        return f"Minister(name='{self.name}')"

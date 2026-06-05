from dataclasses import asdict, dataclass
from typing import Any, Type, TypeVar

T = TypeVar("T", bound="BaseDTO")


@dataclass(frozen=True, eq=True)
class BaseDTO:
    def as_dict(self) -> dict[str, Any]:
        """Converts the DTO to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Creates an instance of the dataclass from a dictionary."""
        return cls(**data)

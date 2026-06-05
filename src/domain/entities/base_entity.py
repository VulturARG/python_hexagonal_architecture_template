from dataclasses import asdict
from typing import Any


class BaseEntity:
    def as_dict(self) -> dict[str, Any]:
        """Return the entity as a plain dictionary. Subclass MUST be decorated with @dataclass."""
        return asdict(self)

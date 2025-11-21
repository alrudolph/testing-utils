from dataclasses import dataclass
from typing import Any, Optional, TypeVar


@dataclass
class Model:
    """
    TODO:
    """
    name: str
    requires: list[str]
    plural: Optional[str] = None

    @property
    def plural_name(self) -> str:
        if self.plural is not None:
            return self.plural

        return f"{self.name}s"


@dataclass
class ModelRequest:
    name: str
    args: dict[str, Any]


@dataclass
class ModelWithRequest:
    """
    TODO:
    """
    model: Model
    request: ModelRequest


T = TypeVar("T")


def or_(*args: T | None) -> T:
    for arg in args:
        if arg is not None:
            return arg

    assert False, "or_() was given no non-None values"

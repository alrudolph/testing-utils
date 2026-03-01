from dataclasses import dataclass
from typing import Any, Optional, TypeGuard, TypeVar, Literal


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


class ModelRequest:
    type: str
    name: str

    @staticmethod
    def create(name: str, args: dict[str, Any]) -> CreateModelRequest:
        return CreateModelRequest(type="create", name=name, args=args)

    @staticmethod
    def is_create_request(instance: ModelRequest) -> TypeGuard[CreateModelRequest]:
        return instance.type == "create"

    @staticmethod
    def existing(name: str, args: dict[str, Any]) -> ExistingModelRequest:
        return ExistingModelRequest(type="existing", name=name, args=args)

    @staticmethod
    def is_existing_request(instance: ModelRequest) -> TypeGuard[ExistingModelRequest]:
        return instance.type == "existing"


@dataclass
class CreateModelRequest(ModelRequest):
    type: Literal["create"]
    name: str
    args: dict[str, Any]


@dataclass
class ExistingModelRequest(ModelRequest):
    type: Literal["existing"]
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

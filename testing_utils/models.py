"""Models and model requests used to represent domain entities and requests to create or retrieve them."""

from dataclasses import dataclass
from typing import Any, Optional, TypeGuard, TypeVar, Literal


@dataclass
class Model:
    """Represents a domain entity."""

    name: str

    requires: list[str]
    """List of names of models that this model depends on. These models will be created or retrieved before this model is created or retrieved."""

    plural: Optional[str] = None
    """In most cases the plural name of the model will just be the name with an 's' at the end, but if this is not the case, you can specify the plural name here."""

    @property
    def plural_name(self) -> str:
        """Returns the plural name of the model, which is used for repository method naming."""
        if self.plural is not None:
            return self.plural

        return f"{self.name}s"


class ModelRequest:
    """Base model request class to create or get a model.

    Use the static methods to create specific request types.
    """

    type: str
    """The type of the request, either "create" or "existing". This is used to determine how to handle the request when creating or retrieving models."""

    name: str
    """The name of the model to create or retrieve."""

    @staticmethod
    def create(name: str, args: dict[str, Any]) -> CreateModelRequest:
        """Create a new CreateModelRequest."""
        return CreateModelRequest(type="create", name=name, args=args)

    @staticmethod
    def is_create_request(instance: ModelRequest) -> TypeGuard[CreateModelRequest]:
        """Check if the given ModelRequest is a CreateModelRequest."""
        return instance.type == "create"

    @staticmethod
    def existing(name: str, args: dict[str, Any]) -> ExistingModelRequest:
        """Create a new ExistingModelRequest."""
        return ExistingModelRequest(type="existing", name=name, args=args)

    @staticmethod
    def is_existing_request(instance: ModelRequest) -> TypeGuard[ExistingModelRequest]:
        """Check if the given ModelRequest is an ExistingModelRequest."""
        return instance.type == "existing"


@dataclass
class CreateModelRequest(ModelRequest):
    """A request to create a new instance of a model.

    This request type should be used in most cases.
    """

    type: Literal["create"]
    name: str
    args: dict[str, Any]


@dataclass
class ExistingModelRequest(ModelRequest):
    """A request to get an existing instance of a model.

    Use this request type if there are for example, there are default rows populated in a database.
    """

    type: Literal["existing"]
    name: str
    args: dict[str, Any]


@dataclass
class ModelWithRequest:
    """Base request to create or retrieve a model alongside model information."""

    model: Model
    request: ModelRequest


T = TypeVar("T")


def or_(*args: T | None) -> T:
    """Return the first non-None value from the given arguments. Raises an AssertionError if all values are None."""
    for arg in args:
        if arg is not None:
            return arg

    raise Exception("or_() was given no non-None values")

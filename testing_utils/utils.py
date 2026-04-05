"""BaseUtils and BaseTransaction classes for users to inherit and implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Optional, Self

from .models import FixtureSpec, Model, or_
from .sort import topological_sort_and_fill

logger = getLogger("testing-utils")


class BaseUtils[TTransaction, TValue](ABC):
    """
    BaseUtils is the base class for the user implemented utils entry point.

    This class provides core logic for creating transactions [TODO:] and retrieving values. \
    Though the user will need to implement some logic to get started.

    Parameters
    ----------
    TTransaction : TypeVar
        The type of the transaction object that will be used in the utils, returned by the `start()` method.
    TValue : TypeVar
        The type of the values that will be created and stored in the utils.

    Notes
    -----
    User Implementation Checklist:

    * Implement `start()` to return a transaction object.
    * Implement `fork()` to return a new instance of the utils class with the same state. Call the underlying `_fork()` method and case the type the implemented utils class.
    * For each entity model implement:
        * The method `_get_{model_plural_name}_repo()` to return the repository for that model. This class will have the get and create methods used in the transaction to call the user's API.
        * The property `{model_name}` to return the instantiation of the entity. You can call `_get_value("{model_name}")` to get the value of the model but should cast it to the correct type.

    When inheriting from this class, set the `_models` attribute in the constructor to a list of `Model` objects with the correct dependencies and names. \
    This will be used to determine the order of creation and retrieval of entities.
    """

    def __init__(
        self,
        models: list[Model],
        name: str = "root",
        parent: Optional[Self] = None,
        fixtures: Optional[list[FixtureSpec]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the BaseUtils.

        This class should be initiated by the user with no arguments passed in. The arguments are used for internal purposes and will be passed in when forking.
        """
        self._data: dict[str, Any] = {}
        self._name = name
        self._parent = parent
        # self._is_setup = False
        # self._setup_complete = False
        self._created_values: dict[str, TValue] = {}
        self._children: list[BaseUtils] = []
        self._parent = parent
        self._requests = or_(requests, [])
        self._models = models
        self._kwargs = kwargs

    @abstractmethod
    def start(self) -> TTransaction:
        """Start a transaction.

        This method should return the user defined transaction object. \
        Consider adding arguments to the utils class constructor if the transaction has dependencies.
        """

    @abstractmethod
    def fork(self, label: str = "") -> Self:
        """Fork the utils to create child state.

        Forking uses existing entities created bu the current utils class and allows you to create new entities on top of that state. \
        This is useful when you have to create multiple entities such as in a 1:N relationship. \
        This method can call the underlying `_fork()` but should type cast to the user implemented utils class.
        """

    def commit(self, tx: TTransaction) -> Self:
        """Commit a transaction to create and retrieve values.

        When the user calls commit on the transaction class this method will be called. \
        This method goes through the model hierarchy and creates and retrieves values based on the requests made in the transaction and any parent dependencies.
        """
        self._commit(tx)

        children = self._children.copy()

        while len(children) > 0:
            child = children.pop(0)
            child._commit(tx)
            children.extend(child._children)

        return self

    async def acommit(self, tx: TTransaction) -> Self:
        """Commit a transaction to create and retrieve values.

        When the user calls commit on the transaction class this method will be called. \
        This method goes through the model hierarchy and creates and retrieves values based on the requests made in the transaction and any parent dependencies.
        """
        await self._acommit(tx)

        children = self._children.copy()

        while len(children) > 0:
            child = children.pop(0)
            await child._acommit(tx)
            children.extend(child._children)

        return self

    def add_request(self, request: ModelRequest) -> None:
        """Add request to generate or retrieve a model.

        This is usually called with in the user implemented transaction class.
        """
        self._requests.append(request)

    def _fork[T: BaseUtils](self, cls: type[T], label: str = "") -> T:
        name = f"{self._name}.{len(self._children)}"

        if len(label) > 0:
            name += f".{label}"

        child = cls(
            name=name,
            parent=self,
            fixtures=self._fixtures.copy(),
            **self._kwargs,
        )

        self._children.append(child)

        return child

    def _find_value(self, name: str) -> TValue | None:
        # if not self._is_setup:
        #     msg = "TestingUtils is not set up. Call setup() before using it."
        #     raise RuntimeError(msg)

        if name in self._created_values:
            return self._created_values[name]

        if self._parent is not None:
            return self._parent._find_value(name)

        # in_request = next(
        #     (request for request in self._requests if request.name == name),
        #     None,
        # )

        # if in_request is None:
        #     raise Exception(f"accessing {name} not in request")

        return None

    def _get_value(self, name: str) -> TValue:
        val = self._find_value(name)

        if val is not None:
            return val

        msg = f"Value {name} not found in created values or parent."

        raise RuntimeError(msg)

    def _create_model(
        self,
        tx: TTransaction,
        model: Model,
        data: dict[str, Any],
    ) -> None:
        repo = getattr(self, f"_get_{model.plural_name}_repo")()

        create_defaults_func = getattr(tx, f"_create_{model.name}_defaults")
        defaults = create_defaults_func(**data)

        value = getattr(repo, f"create_{model.name}")(**defaults)

        self._created_values[model.name] = value

    async def _acreate_model(
        self,
        tx: TTransaction,
        model: Model,
        data: dict[str, Any],
    ) -> None:
        repo = getattr(self, f"_get_{model.plural_name}_repo")()

        create_defaults_func = getattr(tx, f"_create_{model.name}_defaults")
        defaults = create_defaults_func(**data)

        value = await getattr(repo, f"create_{model.name}")(**defaults)

        self._created_values[model.name] = value

    def _get_model(
        self,
        model: Model,
        data: dict[str, Any],
    ) -> None:
        repo = getattr(self, f"_get_{model.plural_name}_repo")()

        value = getattr(repo, f"get_{model.name}")(**data)

        self._created_values[model.name] = value

    async def _aget_model(
        self,
        model: Model,
        data: dict[str, Any],
    ) -> None:
        repo = getattr(self, f"_get_{model.plural_name}_repo")()

        value = await getattr(repo, f"get_{model.name}")(**data)

        self._created_values[model.name] = value

    def _commit(self, tx: TTransaction) -> None:
        models_to_create = topological_sort_and_fill(
            self._models,
            self._requests,
        )

        for model in models_to_create:
            if self._find_value(model.model.name) is not None:
                continue

            req = model.request

            if model.request.is_create_request(req):
                logger.debug(
                    "%s creating %s with args: %s",
                    self._name,
                    model.model.name,
                    req.args,
                )

                self._create_model(tx, model.model, req.args)
            elif model.request.is_existing_request(req):
                logger.debug(
                    "%s getting %s with args: %s",
                    self._name,
                    model.model.name,
                    req.args,
                )

                self._get_model(model.model, req.args)
            else:
                raise ValueError(f"Unknown request type: {req.type}")

        self._requests = []

    async def _acommit(self, tx: TTransaction) -> None:
        models_to_create = topological_sort_and_fill(
            self._models,
            self._requests,
        )

        for model in models_to_create:
            if self._find_value(model.model.name) is not None:
                continue

            req = model.request

            if model.request.is_create_request(req):
                logger.debug(
                    "%s creating %s with args: %s",
                    self._name,
                    model.model.name,
                    req.args,
                )

                await self._acreate_model(tx, model.model, req.args)
            elif model.request.is_existing_request(req):
                logger.debug(
                    "%s getting %s with args: %s",
                    self._name,
                    model.model.name,
                    req.args,
                )

                await self._aget_model(model.model, req.args)
            else:
                raise ValueError(f"Unknown request type: {req.type}")

        self._requests = []


class BaseTransaction:
    """BaseTransaction is the base class for the user implemented transaction object.

    This class should be used to allow the user to specify which entities they want to create (including default values) and retrieve.

    Notes
    -----
    For each entity model implement a `_create_{model_name}_defaults()` method that returns a dict of default values for creating that model. \
    This method will return a dictionary that will be splatted into the create method of the model's repository.

    Use `self._utils._add_request()` to add a request to create or get an entity. Use the `ModelRequest.create()` and `ModelRequest.existing()` static methods to create the request objects.
    """

    def __init__(self, utils: BaseUtils) -> None:
        self._utils = utils

    def commit(self) -> BaseUtils:
        """Commit the transaction to create and retrieve values."""
        self._utils.commit(self)

        return self._utils

    async def acommit(self) -> BaseUtils:
        """Commit the transaction to create and retrieve values."""
        await self._utils.acommit(self)

        return self._utils

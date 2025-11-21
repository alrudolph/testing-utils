from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Optional, Self

from .models import Model, ModelRequest, or_
from .sort import topological_sort_and_fill

logger = getLogger("testing-utils")


class BaseUtils[TTransaction, TValue](ABC):

    def __init__(
        self,
        name: str = "root",
        parent: Optional[Self] = None,
        requests: Optional[list[ModelRequest]] = None,
        **kwargs: Any,
    ) -> None:
        self._data: dict[str, Any] = {}
        self._name = name
        self._parent = parent
        # self._is_setup = False
        # self._setup_complete = False
        self._created_values: dict[str, TValue] = {}
        self._children: list[BaseUtils] = []
        self._parent = parent
        self._requests = or_(requests, [])
        self._models: list[Model] = []
        self._kwargs = kwargs

    def _find_value(self, name: str) -> TValue | None:
        # if not self._is_setup:
        #     msg = "TestingUtils is not set up. Call setup() before using it."
        #     raise RuntimeError(msg)

        if name in self._created_values:
            return self._created_values[name]

        if self._parent is not None:
            return self._parent._find_value(name)

        in_request = next(
            (request for request in self._requests if request.name == name),
            None,
        )

        # if self._setup_complete and in_request is None:
        #     raise Exception(f"accessing {name} not in request")

        return None

    def _add_request(self, request: ModelRequest) -> None:
        self._requests.append(request)

    def _get_value(self, name: str) -> TValue:
        val = self._find_value(name)

        if val is not None:
            return val

        msg = f"Value {name} not found in created values or parent."
        raise RuntimeError(msg)

    @abstractmethod
    def start(self) -> TTransaction:
        """
        TODO:
        """

    #
    # TODO: support sync too
    #
    async def _dispatch(
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

    #
    # TODO: support sync too
    #
    async def commit(self, tx: TTransaction) -> None:
        """
        TODO:
        """
        await self._commit(tx)

        children = self._children.copy()

        while len(children) > 0:
            child = children.pop(0)
            await child._commit(tx)
            children.extend(child._children)

    #
    # TODO: support sync too
    #
    async def _commit(self, tx: TTransaction) -> None:
        models_to_create = topological_sort_and_fill(
            self._models,
            self._requests,
        )

        for model in models_to_create:
            if self._find_value(model.model.name) is not None:
                continue

            logger.debug(
                "%s creating %s with args: %s",
                self._name,
                model.model.name,
                model.request.args,
            )

            await self._dispatch(tx, model.model, model.request.args)

        self._requests = []

    @abstractmethod
    def fork(self, label: str = "") -> Self:
        """
        TODO:
        """

    def _fork[T: BaseUtils](self, cls: type[T], label: str = "") -> T:
        name = f"{self._name}.{len(self._children)}"

        if len(label) > 0:
            name += f".{label}"

        child = cls(
            name=name,
            parent=self,
            requests=self._requests.copy(),
            **self._kwargs,
        )
        self._children.append(child)
        return child

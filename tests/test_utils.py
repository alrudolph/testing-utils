from __future__ import annotations

from testing_utils import BaseUtils, ModelRequest, Model, BaseTransaction
from typing import Optional, Self, Any, cast
import pytest

pytest_plugins = ("pytest_asyncio",)


class Transaction(BaseTransaction):

    def __init__(self, utils: Utils) -> None:
        self._utils = utils

    def commit(self) -> Utils:
        return cast(Utils, super().commit())

    async def acommit(self) -> Utils:
        return cast(Utils, await super().acommit())

    def with_a(self, *, value: int = 0) -> Self:
        self._utils.add_request(ModelRequest.create("a", {"value": value}))
        return self

    def with_existing_a(self, *, value: int = 0) -> Self:
        self._utils.add_request(ModelRequest.existing("a", {"value": value}))
        return self

    def _create_a_defaults(self, value: int = 0) -> dict[str, Any]:
        return {"value": value}

    def with_b(self, *, value: int = 0) -> Self:
        self._utils.add_request(ModelRequest.create("b", {"value": value}))
        return self

    def with_existing_b(self, *, value: int = 0) -> Self:
        self._utils.add_request(ModelRequest.existing("b", {"value": value}))
        return self

    def _create_b_defaults(self, value: int = 0) -> dict[str, Any]:
        return {"value": value}

    def with_c(self, *, value: int = 0) -> Self:
        self._utils.add_request(ModelRequest.create("c", {"value": value}))
        return self

    def with_existing_c(self, *, value: int = 0) -> Self:
        self._utils.add_request(ModelRequest.existing("c", {"value": value}))
        return self

    def _create_c_defaults(self, value: int = 0) -> dict[str, Any]:
        return {"value": value}


class Utils(BaseUtils[Transaction, object]):

    def __init__(
        self,
        repos: dict[str, Any],
        name: str = "root",
        parent: Optional[Self] = None,
        requests: Optional[list[ModelRequest]] = None,
    ) -> None:
        super().__init__(
            [
                Model(name="a", requires=[]),
                Model(name="b", requires=[]),
                Model(name="c", requires=["a"]),
            ],
            name,
            parent,
            requests,
        )
        self._kwargs = repos

    def start(self) -> Transaction:
        return Transaction(self)

    def fork(self, label: str = "") -> Utils:
        child = self._fork(Utils, label)
        return child

    def _get_as_repo(self) -> AsyncARepo:
        return self._kwargs["a_repo"]

    @property
    def a(self) -> A:
        return cast(A, self._get_value("a"))

    def _get_bs_repo(self) -> AsyncBRepo:
        return self._kwargs["b_repo"]

    @property
    def b(self) -> B:
        return cast(B, self._get_value("b"))

    def _get_cs_repo(self) -> AsyncCRepo:
        return self._kwargs["c_repo"]

    @property
    def c(self) -> C:
        return cast(C, self._get_value("c"))


class AsyncARepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    async def create_a(self, *, value: int) -> A:
        self.log.append(ModelRequest.create("a", {"value": value}))
        return A()

    async def get_a(self, *, value: int) -> A:
        self.log.append(ModelRequest.existing("a", {"value": value}))
        return A()


class AsyncBRepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    async def create_b(self, *, value: int) -> B:
        self.log.append(ModelRequest.create("b", {"value": value}))
        return B()

    async def get_b(self, *, value: int) -> B:
        self.log.append(ModelRequest.existing("b", {"value": value}))
        return B()


class AsyncCRepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    async def create_c(self, *, value: int) -> C:
        self.log.append(ModelRequest.create("c", {"value": value}))
        return C()

    async def get_c(self, *, value: int) -> C:
        self.log.append(ModelRequest.existing("c", {"value": value}))
        return C()


class ARepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    def create_a(self, *, value: int) -> A:
        self.log.append(ModelRequest.create("a", {"value": value}))
        return A()

    def get_a(self, *, value: int) -> A:
        self.log.append(ModelRequest.existing("a", {"value": value}))
        return A()


class BRepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    def create_b(self, *, value: int) -> B:
        self.log.append(ModelRequest.create("b", {"value": value}))
        return B()

    def get_b(self, *, value: int) -> B:
        self.log.append(ModelRequest.existing("b", {"value": value}))
        return B()


class CRepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    def create_c(self, *, value: int) -> C:
        self.log.append(ModelRequest.create("c", {"value": value}))
        return C()

    def get_c(self, *, value: int) -> C:
        self.log.append(ModelRequest.existing("c", {"value": value}))
        return C()


class A: ...


class B: ...


class C: ...


def test_utils() -> None:
    a_repo = ARepo()
    b_repo = BRepo()
    c_repo = CRepo()

    utils = Utils(
        {
            "a_repo": a_repo,
            "b_repo": b_repo,
            "c_repo": c_repo,
        }
    )

    res = utils.start().with_b(value=20).with_c(value=30).commit()

    assert a_repo.log == [ModelRequest.create("a", {"value": 0})]
    assert b_repo.log == [ModelRequest.create("b", {"value": 20})]
    assert c_repo.log == [ModelRequest.create("c", {"value": 30})]

    assert isinstance(res.a, A)
    assert isinstance(res.b, B)
    assert isinstance(res.c, C)


def test_with_existing() -> None:
    a_repo = ARepo()
    b_repo = BRepo()
    c_repo = CRepo()

    utils = Utils(
        {
            "a_repo": a_repo,
            "b_repo": b_repo,
            "c_repo": c_repo,
        }
    )

    res = utils.start().with_existing_a(value=20).with_c(value=30).commit()

    assert a_repo.log == [ModelRequest.existing("a", {"value": 20})]
    assert b_repo.log == []
    assert c_repo.log == [ModelRequest.create("c", {"value": 30})]

    assert isinstance(res.a, A)

    with pytest.raises(RuntimeError):
        res.b

    assert isinstance(res.c, C)


@pytest.mark.asyncio
async def test_async_utils() -> None:
    a_repo = AsyncARepo()
    b_repo = AsyncBRepo()
    c_repo = AsyncCRepo()

    utils = Utils(
        {
            "a_repo": a_repo,
            "b_repo": b_repo,
            "c_repo": c_repo,
        }
    )

    res = await utils.start().with_b(value=20).with_c(value=30).acommit()

    assert a_repo.log == [ModelRequest.create("a", {"value": 0})]
    assert b_repo.log == [ModelRequest.create("b", {"value": 20})]
    assert c_repo.log == [ModelRequest.create("c", {"value": 30})]

    assert isinstance(res.a, A)
    assert isinstance(res.b, B)
    assert isinstance(res.c, C)


@pytest.mark.asyncio
async def test_async_with_existing() -> None:
    a_repo = AsyncARepo()
    b_repo = AsyncBRepo()
    c_repo = AsyncCRepo()

    utils = Utils(
        {
            "a_repo": a_repo,
            "b_repo": b_repo,
            "c_repo": c_repo,
        }
    )

    res = await utils.start().with_existing_a(value=20).with_c(value=30).acommit()

    assert a_repo.log == [ModelRequest.existing("a", {"value": 20})]
    assert b_repo.log == []
    assert c_repo.log == [ModelRequest.create("c", {"value": 30})]

    assert isinstance(res.a, A)

    with pytest.raises(RuntimeError):
        res.b

    assert isinstance(res.c, C)

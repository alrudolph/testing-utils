from __future__ import annotations

from testing_utils import BaseUtils, ModelRequest, Model
from typing import Optional, Self, Any, cast
import pytest

pytest_plugins = ("pytest_asyncio",)


class Transaction:

    def __init__(self, utils: Utils) -> None:
        self._utils = utils

    async def commit(self) -> Utils:
        await self._utils.commit(self)
        return self._utils

    def with_a(self, *, value: int = 0) -> Self:
        self._utils._add_request(ModelRequest.create("a", {"value": value}))
        return self

    def with_existing_a(self, *, value: int = 0) -> Self:
        self._utils._add_request(ModelRequest.existing("a", {"value": value}))
        return self

    def _create_a_defaults(self, value: int = 0) -> dict[str, Any]:
        return {"value": value}

    def with_b(self, *, value: int = 0) -> Self:
        self._utils._add_request(ModelRequest.create("b", {"value": value}))
        return self

    def with_existing_b(self, *, value: int = 0) -> Self:
        self._utils._add_request(ModelRequest.existing("b", {"value": value}))
        return self

    def _create_b_defaults(self, value: int = 0) -> dict[str, Any]:
        return {"value": value}

    def with_c(self, *, value: int = 0) -> Self:
        self._utils._add_request(ModelRequest.create("c", {"value": value}))
        return self

    def with_existing_c(self, *, value: int = 0) -> Self:
        self._utils._add_request(ModelRequest.existing("c", {"value": value}))
        return self

    def _create_c_defaults(self, value: int = 0) -> dict[str, Any]:
        return {"value": value}


class Utils(BaseUtils[Transaction, object]):

    def __init__(
        self,
        a_repo: ARepo,
        b_repo: BRepo,
        c_repo: CRepo,
        name: str = "root",
        parent: Optional[Self] = None,
        requests: Optional[list[ModelRequest]] = None,
    ) -> None:
        super().__init__(name, parent, requests)
        self._models = [
            Model(name="a", requires=[]),
            Model(name="b", requires=[]),
            Model(name="c", requires=["a"]),
        ]
        self._a_repo = a_repo
        self._b_repo = b_repo
        self._c_repo = c_repo
        self._kwargs = {
            "a_repo": a_repo,
            "b_repo": b_repo,
            "c_repo": c_repo,
        }

    def start(self) -> Transaction:
        return Transaction(self)

    def fork(self, label: str = "") -> Utils:
        child = self._fork(Utils, label)
        return child

    def _get_as_repo(self) -> ARepo:
        return self._a_repo

    @property
    def a(self) -> A:
        return cast(A, self._get_value("a"))

    def _get_bs_repo(self) -> BRepo:
        return self._b_repo

    @property
    def b(self) -> B:
        return cast(B, self._get_value("b"))

    def _get_cs_repo(self) -> CRepo:
        return self._c_repo

    @property
    def c(self) -> C:
        return cast(C, self._get_value("c"))


class ARepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    async def create_a(self, *, value: int) -> A:
        self.log.append(ModelRequest.create("a", {"value": value}))
        return A()

    async def get_a(self, *, value: int) -> A:
        self.log.append(ModelRequest.existing("a", {"value": value}))
        return A()


class BRepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    async def create_b(self, *, value: int) -> B:
        self.log.append(ModelRequest.create("b", {"value": value}))
        return B()

    async def get_b(self, *, value: int) -> B:
        self.log.append(ModelRequest.existing("b", {"value": value}))
        return B()


class CRepo:

    def __init__(self) -> None:
        self.log: list[ModelRequest] = []

    async def create_c(self, *, value: int) -> C:
        self.log.append(ModelRequest.create("c", {"value": value}))
        return C()

    async def get_c(self, *, value: int) -> C:
        self.log.append(ModelRequest.existing("c", {"value": value}))
        return C()


class A: ...


class B: ...


class C: ...


@pytest.mark.asyncio
async def test_utils() -> None:
    a_repo = ARepo()
    b_repo = BRepo()
    c_repo = CRepo()

    utils = Utils(a_repo, b_repo, c_repo)

    await utils.start().with_b(value=20).with_c(value=30).commit()

    assert a_repo.log == [ModelRequest.create("a", {"value": 0})]
    assert b_repo.log == [ModelRequest.create("b", {"value": 20})]
    assert c_repo.log == [ModelRequest.create("c", {"value": 30})]


@pytest.mark.asyncio
async def test_with_existing() -> None:
    a_repo = ARepo()
    b_repo = BRepo()
    c_repo = CRepo()

    utils = Utils(a_repo, b_repo, c_repo)

    await utils.start().with_existing_a(value=20).with_c(value=30).commit()

    assert a_repo.log == [ModelRequest.existing("a", {"value": 20})]
    assert b_repo.log == []
    assert c_repo.log == [ModelRequest.create("c", {"value": 30})]

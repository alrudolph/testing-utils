from __future__ import annotations

from typing import Self

from pydantic import BaseModel

from testing_utils import BaseUtils, Model


class Transaction:
    """
    TODO:
    """

    def __init__(self, utils: EndpointUtils) -> None:
        self._utils = utils

    async def commit(self) -> EndpointUtils:
        await self._utils.commit(self)
        return self._utils


class EndpointUtils(BaseUtils[Transaction, BaseModel]):
    """
    TODO:
    """

    # TODO: add types
    def __init__(self, client, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client = client
        self._models = [
            Model(name="", requires=[])
        ]

    def fork(self, label: str = "") -> Self:
        return self._fork(EndpointUtils, label)

    def start(self) -> Transaction:
        return Transaction(self)

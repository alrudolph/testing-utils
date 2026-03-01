from __future__ import annotations

from typing import Self, cast

from pydantic import BaseModel

from testing_utils import BaseUtils


class Transaction:
    """
    TODO:
    """

    def __init__(self, utils: DatabaseUtils) -> None:
        self._utils = utils

    async def commit(self) -> DatabaseUtils:
        await self._utils.commit(self)
        return self._utils


class DatabaseUtils(BaseUtils[Transaction, BaseModel]):
    """
    TODO:
    """

    # TODO: add types
    def __init__(self, db, **kwargs) -> None:
        super().__init__(**kwargs)
        self._db = db

    def fork(self, label: str = "") -> DatabaseUtils:
        forked = self._fork(DatabaseUtils, label)
        return cast(DatabaseUtils, forked)

    def start_transaction(self) -> Transaction:
        return Transaction(self)

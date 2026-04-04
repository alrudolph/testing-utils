from __future__ import annotations

from typing import Any, Self, cast

from pydantic import BaseModel
from testing_utils import BaseUtils, BaseTransaction, Model, ModelRequest
from testing_utils.utils import or_
from typing import Optional


def test_company_membership():
    db = Database()
    utils = DatabaseUtils(db)

    membership_util = utils.start().with_membership(role="admin").commit()

    # access created membership:
    assert membership_util.membership.role == "admin"

    # Creating membership created a company:
    retrieved_company = db.get_table("companies").get(
        id=membership_util.membership.company_id
    )

    print(retrieved_company.company_name)

    # Creating membership created a user:
    retrieved_user = db.get_table("users").get(id=membership_util.membership.user_id)

    print(retrieved_user.user_name)


class Transaction(BaseTransaction):

    def __init__(self, utils: DatabaseUtils) -> None:
        self._utils = utils

    def commit(self) -> DatabaseUtils:
        return cast(DatabaseUtils, super().commit())

    def with_user(self, user_name: Optional[str] = None) -> Self:
        self._utils.add_request(ModelRequest.create("user", {"user_name": user_name}))
        return self

    def _create_user_defaults(self, user_name: Optional[str] = None) -> dict[str, Any]:
        return {"user_name": or_(user_name, "default_user_name")}

    def with_company(self, company_name: Optional[str] = None) -> Self:
        self._utils.add_request(
            ModelRequest.create("company", {"company_name": company_name})
        )
        return self

    def _create_company_defaults(
        self,
        company_name: Optional[str] = None,
    ) -> dict[str, Any]:
        return {"company_name": or_(company_name, "default_company_name")}

    def with_membership(self, role: Optional[str] = None) -> Self:
        self._utils.add_request(ModelRequest.create("membership", {"role": role}))
        return self

    def _create_membership_defaults(self, role: Optional[str] = None) -> dict[str, Any]:
        return {
            "company_id": self._utils.company.id,
            "user_id": self._utils.user.id,
            "role": or_(role, "default_role"),
        }


class DatabaseUtils(BaseUtils[Transaction, BaseModel]):

    def __init__(self, db: Database, **kwargs) -> None:
        super().__init__(
            [
                Model(name="company", requires=[], plural="companies"),
                Model(name="user", requires=[]),
                Model(name="membership", requires=["company", "user"]),
            ],
            **kwargs,
        )
        self._db = db

    def start(self) -> Transaction:
        return Transaction(self)

    def fork(self, label: str = "") -> DatabaseUtils:
        child = self._fork(DatabaseUtils, label)
        return child

    def _get_companies_repo(self) -> CompaniesRepo:
        return CompaniesRepo(self._db)

    @property
    def company(self) -> Company:
        return cast(Company, self._get_value("company"))

    def _get_users_repo(self) -> UsersRepo:
        return UsersRepo(self._db)

    @property
    def user(self) -> User:
        return cast(User, self._get_value("user"))

    def _get_memberships_repo(self) -> MembershipsRepo:
        return MembershipsRepo(self._db)

    @property
    def membership(self) -> Membership:
        return cast(Membership, self._get_value("membership"))


# Existing models:


class BaseTableModel(BaseModel):
    id: int


class Company(BaseTableModel):
    company_name: str


class User(BaseTableModel):
    user_name: str


class Membership(BaseTableModel):
    company_id: int
    user_id: int
    role: str


# Existing repos:


class CompaniesRepo:

    def __init__(self, db: Database) -> None:
        self._db = db

    def create_company(self, *, company_name: str) -> Company:
        table = self._db.get_table("companies")

        company = Company(id=table.get_next_id(), company_name=company_name)

        return table.add(company)

    def get_company(self, *, company_id: int) -> Company:
        table = self._db.get_table("companies")

        return table.get(id=company_id)


class UsersRepo:

    def __init__(self, db: Database) -> None:
        self._db = db

    def create_user(self, *, user_name: str) -> User:
        table = self._db.get_table("users")

        user = User(id=table.get_next_id(), user_name=user_name)

        return table.add(user)

    def get_user(self, *, user_id: int) -> User:
        table = self._db.get_table("users")

        return table.get(id=user_id)


class MembershipsRepo:

    def __init__(self, db: Database) -> None:
        self._db = db

    def create_membership(
        self,
        *,
        company_id: int,
        user_id: int,
        role: str,
    ) -> Membership:
        table = self._db.get_table("memberships")

        membership = Membership(
            id=table.get_next_id(),
            company_id=company_id,
            user_id=user_id,
            role=role,
        )

        return table.add(membership)

    def get_membership(self, *, membership_id: int) -> Membership:
        table = self._db.get_table("memberships")

        return table.get(id=membership_id)


class Database:
    """Simple in-memory database implementation for demonstration purposes."""

    def __init__(self) -> None:
        self._values: dict[str, Table] = {}

    def get_table(self, name: str) -> Table:
        if name not in self._values:
            self._values[name] = Table()

        return self._values[name]


class Table[Value: BaseTableModel]:
    """Simple in-memory table implementation for demonstration purposes."""

    def __init__(self) -> None:
        self._values: list[Value] = []

    def get_next_id(self) -> int:
        return len(self._values) + 1

    def add(self, value: Value) -> Value:
        self._values.append(value)
        return value

    def get(self, id: int) -> Value:
        return next(value for value in self._values if value.id == id)

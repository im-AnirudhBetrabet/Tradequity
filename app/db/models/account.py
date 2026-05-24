"""
Account ORM model definitions.

This module defines financial account entities used by the Tradequity
double-entry ledger systems.

Accounts represent ownership buckets for financial value, while balances
are derived dynamically from immutable ledger transactions.
"""

from datetime import datetime
from enum     import Enum
from uuid     import UUID

from sqlalchemy     import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base  import Base
from app.db.enums import AccountType

class Account(Base):
    """
    Financial account model.

    Accounts represent logical ownership buckets for value movement within
    the double-entry ledger system.

    Account balances are not stored directly and must be derived from
    immutable ledger transaction history.

    Attributes:
        id:
            Unique account identifier.

        user_id:
            Owning user profile UUID for user-linked accounts.

        account_type:
            Logical account classification

        currency:
            Account currency code.

        is_active:
            Indicates whether the account is operational.
    """

    __tablename__ = "accounts"

    id          : Mapped[UUID]        = mapped_column(primary_key=True)
    user_id     : Mapped[UUID]        = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=True)
    account_type: Mapped[AccountType] = mapped_column(SqlEnum(AccountType, name="account_type",native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    currency    : Mapped[str]         = mapped_column(Text, nullable=False)
    is_active   : Mapped[bool]        = mapped_column(Boolean, nullable=False, default=True)
    created_at  : Mapped[datetime]    = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


"""
Profile ORM model definitions.

This module defines the application profile entity used for user identity,
authorization, and operational metadata.

Profiles are application-specific user records linked ot authenticated
Supabase users via shared UUID identity.
"""

from datetime import datetime
from decimal import Decimal
from uuid     import UUID

from sqlalchemy import Boolean, Numeric, Enum as SqlEnum
from sqlalchemy import DateTime
from sqlalchemy import Text

from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base    import Base
from app.db.enums   import UserRole


class Profile(Base):
    """
    Application user profile model.

    This entity stores application-level user metadata and authorization
    attributes separate from Supabase authentication records.

    Attributes:
        id:
            Supabase-authenticated user UUID.

        full_name:
            Human-readable display name.

        is_active:
            Indicates whether the user account is active.

        user_role:
            Indicates whether the user has administrative privileges.

        created_at:
            Record creation timestamp.

        updated_at:
            Last modification timestamp.
    """

    __tablename__ = "profiles"

    id                      : Mapped[UUID]       = mapped_column(primary_key=True)
    full_name               : Mapped[str | None] = mapped_column(Text   , nullable=True)
    is_active               : Mapped[bool]       = mapped_column(Boolean, nullable=False, default=True)
    role                    : Mapped[str ]       = mapped_column(SqlEnum(UserRole, name="user_role",native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, default=UserRole.INVESTOR)
    created_at              : Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at              : Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    minimum_profit_threshold: Mapped[Decimal]    = mapped_column(Numeric(10, 8), nullable=False, default=Decimal("0.08"))


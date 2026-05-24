"""
Position allocation ORM model definitions.

This module defines beneficial ownership allocation records linking
individual users to pooled master investment positions.

Allocations represent user-specific ownership slices of platform-held
investment lots and are the authoritative source for per-user exposure,
cost basis, and realization accounting.
"""

from datetime       import datetime
from decimal        import Decimal
from uuid           import UUID
from sqlalchemy     import DateTime,Enum as SqlEnum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base    import Base
from app.db.enums   import AllocationStatus


class PositionAllocation(Base):
    """
    Beneficial ownership allocation record.

    Represents an individual user's ownership share within a pooled
    master investment position.

    Attributes:
        id:
            Unique allocation identifier.

        user_id:
            Owning user profile identifier.

        position_id:
            Referenced pooled master position.

        original_quantity:
            Initial allocated quantity.

        remaining_quantity:
            Quantity not yet realized.

        original_cost:
            Initial user cost basis.

        remaining_cost:
            Unrecovered cost basis for open quantity.

        status:
            Allocation lifecycle state.

        opened_at:
            Allocation opening timestamp.

        closed_at:
            Allocation closure timestamp.

        created_at:
            Record creation timestamp.
    """

    __tablename__   = "position_allocations"
    __mapper_args__ = {"eager_defaults": True}

    id                : Mapped[UUID]             = mapped_column(primary_key=True)
    user_id           : Mapped[UUID]             = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"),nullable=False)
    position_id       : Mapped[UUID]             = mapped_column(ForeignKey("master_positions.id", ondelete="RESTRICT"),nullable=False)
    original_quantity : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    remaining_quantity: Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    original_cost     : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    remaining_cost    : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    status            : Mapped[AllocationStatus] = mapped_column(SqlEnum(AllocationStatus, name="allocation_status", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]),nullable=False)
    opened_at         : Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at         : Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)
    created_at        : Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
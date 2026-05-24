"""
Withdrawal request ORM model definitions.

This module defines withdrawal workflow records used for user fund exit
requests and administrative processing.

Withdrawal requests are operational workflow entities and do not directly
represent financial ledger movement.
"""

from datetime       import datetime
from decimal        import Decimal
from uuid           import UUID
from sqlalchemy     import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from app.db.base    import Base
from app.db.enums   import WithdrawalStatus


class WithdrawalRequest(Base):
    """
    User withdrawal workflow record.

    Represents a user withdrawal request and its administrative lifecycle.

    Attributes:
        id:
            Unique withdrawal request identifier.

        user_id:
            Requesting user profile identifier.

        requested_amount:
            User requested withdrawal amount.

        principal_amount:
            Principal basis used for penalty calculations.

        penalty_pct:
            Applied penalty percentage.

        penalty_amount:
            Absolute penalty deducted.

        net_payout:
            Final payout amount after deductions.

        liquidation_required:
            Indicates whether asset liquidation is required.

        status:
            Workflow lifecycle state.

        requested_at:
            User request timestamp.

        processed_at:
            Administrative processing timestamp.

        completed_at:
            Completion timestamp.

        processed_by:
            Administrative processor identifier.

        notes:
            Operational notes.

        created_at:
            Record creation timestamp.
    """

    __tablename__   = "withdrawal_requests"
    __mapper_args__ = {"eager_defaults": True}

    id                  : Mapped[UUID]             = mapped_column(primary_key=True)
    user_id             : Mapped[UUID]             = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"),nullable=False)
    requested_amount    : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    principal_amount    : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    penalty_pct         : Mapped[Decimal]          = mapped_column(Numeric(10, 4),nullable=False)
    penalty_amount      : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    net_payout          : Mapped[Decimal]          = mapped_column(Numeric(20, 8),nullable=False)
    liquidation_required: Mapped[bool]             = mapped_column(Boolean,nullable=False)
    status              : Mapped[WithdrawalStatus] = mapped_column(SqlEnum(WithdrawalStatus, name="withdrawal_status", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    requested_at        : Mapped[datetime]         = mapped_column(DateTime(timezone=True),nullable=False)
    processed_at        : Mapped[datetime | None]  = mapped_column(DateTime(timezone=True),nullable=True)
    completed_at        : Mapped[datetime | None]  = mapped_column(DateTime(timezone=True),nullable=True)
    processed_by        : Mapped[UUID | None]      = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"),nullable=True)
    notes               : Mapped[str | None]       = mapped_column(Text,nullable=True)
    created_at          : Mapped[datetime]         = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
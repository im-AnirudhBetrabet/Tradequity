"""
Allocation realization ORM model definitions.

This module defines realization event records representing the financial
impact of sell executions on user-specific investment allocations.

Realization records are immutable accounting snapshots and provide the
authoritative audit trail for realized gains, fees, and credited proceeds.
"""

from datetime       import datetime
from decimal        import Decimal
from uuid           import UUID
from sqlalchemy     import DateTime
from sqlalchemy     import ForeignKey
from sqlalchemy     import Numeric
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func
from app.db.base    import Base


class AllocationRealization(Base):
    """
    Immutable user allocation realization record.

    Represents the realized financial impact of a sell execution against
    a specific user allocation.

    Attributes:
        id:
            Unique realization identifier.

        allocation_id:
            Referenced user allocation.

        trade_execution_id:
            Referenced sell trade execution.

        realized_quantity:
            Quantity realized from the allocation.

        realized_cost:
            Cost basis associated with realized quantity.

        execution_price:
            Per-unit sell execution price.

        gross_proceeds:
            Gross proceeds before fees.

        realized_pnl:
            Gross realized profit or loss.

        performance_fee:
            Platform fee charged on realized gains.

        net_credit:
            Net amount credited to the user.

        realized_at:
            Business realization timestamp.

        created_at:
            Record creation timestamp.
    """

    __tablename__   = "allocation_realizations"
    __mapper_args__ = {"eager_defaults": True}

    id                : Mapped[UUID]     = mapped_column(primary_key=True)
    allocation_id     : Mapped[UUID]     = mapped_column(ForeignKey("position_allocations.id", ondelete="RESTRICT"),nullable=False)
    trade_execution_id: Mapped[UUID]     = mapped_column(ForeignKey("trade_executions.id", ondelete="RESTRICT"),nullable=False)
    realized_quantity : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    realized_cost     : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    execution_price   : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    gross_proceeds    : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    realized_pnl      : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    performance_fee   : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    net_credit        : Mapped[Decimal]  = mapped_column(Numeric(20, 8),nullable=False)
    realized_at       : Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)
    created_at        : Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
"""
Trade execution ORM model definitions.

This module defines immutable trade execution records representing
platform buy and sell actions.

Trade executions are authoritative execution events and form the basis
for position creation, allocation accounting, and realization workflows.
"""

from datetime import datetime
from decimal  import Decimal
from uuid     import UUID

from sqlalchemy     import DateTime, Enum as SqlEnum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base  import Base
from app.db.enums import AssetType, TradeType

class TradeExecution(Base):
    """
    Immutable trade execution record.

    Represents a platform-level executed buy or sell trade.

    Buy trades:
        - create master positions.
        - establish user allocations.

    Sell trades:
        - unwind existing positions.
        - trigger realization workflows

    Attributes:
        id:
            Unique trade execution identifier.

        trade_type:
            Buy or sell execution direction

        symbol:
            Exchange trading symbol.

        instrument_name:
            Human-readable instrument name.

        asset_type:
            Investment asset classification.

        position_id:
            Associated master position for sell trades

        quantity:
            Executed trade quantity.

        price:
            Per-unit execution price.

        charges:
            Trade-associated execution charges.

        executed_at:
            Timestamp when the trade was executed.

        entered_by:
            Administrative user who recorded the trade.

        notes:
            Option operational notes

        created_at:
            Record creation timestamp
    """
    __tablename__   = "trade_executions"
    __mapper_args__ = {"eager_defaults": True}

    id             : Mapped[UUID]        = mapped_column(primary_key=True,)
    trade_type     : Mapped[TradeType]   = mapped_column(SqlEnum(TradeType, name="trade_type", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False,)
    symbol         : Mapped[str]         = mapped_column(Text,nullable=False,)
    instrument_name: Mapped[str]         = mapped_column(Text,nullable=False,)
    asset_type     : Mapped[AssetType]   = mapped_column(SqlEnum(AssetType, name="asset_type", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]),nullable=False,)
    position_id    : Mapped[UUID | None] = mapped_column(ForeignKey("master_positions.id", ondelete="RESTRICT"),nullable=True,)
    quantity       : Mapped[Decimal]     = mapped_column(Numeric(20, 8),nullable=False,)
    price          : Mapped[Decimal]     = mapped_column(Numeric(20, 8),nullable=False,)
    charges        : Mapped[Decimal]     = mapped_column(Numeric(20, 8),nullable=False,)
    executed_at    : Mapped[datetime]    = mapped_column(DateTime(timezone=True),nullable=False,)
    entered_by     : Mapped[UUID]        = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"),nullable=False,)
    notes          : Mapped[str | None]  = mapped_column(Text,nullable=True,)
    created_at     : Mapped[datetime]    = mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),)
"""
Master position ORM model definitions.

This module defines pooled investment position records representing
platform-held investment lots created through executed buy trades.

Master positions serve as the authoritative ownership container from
which individual user allocations derive beneficial ownership.
"""

from datetime import datetime
from decimal  import Decimal
from uuid     import UUID

from sqlalchemy     import DateTime, Enum as SqlEnum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base  import Base
from app.db.enums import AssetType, PositionStatus

class MasterPosition(Base):
    """
    Pooled investment position record.

    Represents a platform-level investment lot acquired through a buy
    execution and partially or fully owned by one or more users.

    Attributes:
        id:
            Unique master position identifier.

        originating_trade_id:
            Buy trade that created this position.

        symbol:
            Exchange trading symbol.

        instrument_name:
            Human-readable instrument name.

        asset_type:
            Investment asset classification.

        total_quantity:
            Original acquired quantity.

        remaining_quantity:
            Quantity not yet liquidated.

        status:
            Position lifecycle state.

        opened_at:
            Position opening timestamp.

        closed_at:
            Position closure timestamp.

        created_at:
            Record creation timestamp.
    """

    __tablename__   = "master_positions"
    __mapper_args__ = {"eager_defaults": True}

    id                  : Mapped[UUID]            = mapped_column(primary_key=True)
    originating_trade_id: Mapped[UUID]            = mapped_column(ForeignKey("trade_executions.id", ondelete="RESTRICT"), nullable=False)
    symbol              : Mapped[str]             = mapped_column(Text, nullable=False)
    instrument_name     : Mapped[str]             = mapped_column(Text, nullable=False)
    asset_type          : Mapped[AssetType]       = mapped_column(SqlEnum(AssetType, name="asset_type", native_enum=True), nullable=False)
    total_quantity      : Mapped[Decimal]         = mapped_column(Numeric(20, 8), nullable=False)
    remaining_quantity  : Mapped[Decimal]         = mapped_column(Numeric(20, 8), nullable=False)
    status              : Mapped[PositionStatus]  = mapped_column(SqlEnum(PositionStatus, name="position_status", native_enum=True), nullable=False)
    opened_at           : Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at           : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at          : Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

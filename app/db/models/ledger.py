"""
Ledger transaction ORM model definitions.

This module defines immutable double-entry financial ledger transactions
used for all monetary movement within the Tradequity platform.

Design principles:
    - Immutable financial event history.
    - Double-entry accounting integrity.
    - Explicit transaction traceability.
    - Database-enforced monetary consistency.
"""

from datetime import datetime
from decimal  import Decimal
from enum     import Enum
from uuid     import UUID

from sqlalchemy     import DateTime, Enum as SqlEnum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base  import Base
from app.db.enums import TransactionReferenceType



class LedgerTransaction(Base):
    """
    Immutable financial ledger transaction.

    Represents a single double-entry monetary movement between two
    financial accounts.

    Attributes:
        id:
            Unique transaction identifier.

        from_account_id:
            Source account identifier.

        to_account_id:
            Destination account identifier.

        amount:
            Monetary amount transferred.

        reference_type:
            Business domain classification for traceability.

        reference_id:
            Related main entity identifier.

        ledger_metadata:
            Human-readable transaction description.

        created_at:
            Transaction creation timestamp.
    """

    __tablename__   = "ledger_transactions"
    __mapper_args__ = { "eager_defaults": True }

    id             : Mapped[UUID]                     = mapped_column(primary_key=True)
    from_account_id: Mapped[UUID]                     = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    to_account_id  : Mapped[UUID]                     = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    amount         : Mapped[Decimal]                  = mapped_column(Numeric(20, 8), nullable=False)
    reference_type : Mapped[TransactionReferenceType] = mapped_column(SqlEnum(TransactionReferenceType, name="ledger_reference_type", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    reference_id   : Mapped[UUID]                     = mapped_column(nullable=False)
    ledger_metadata: Mapped[dict | None]              = mapped_column("metadata",JSONB, nullable=True)
    created_at     : Mapped[datetime]                 = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    

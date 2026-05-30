"""
Capital lot persistence model.

Tracks principal capital lots for FIFO redemption accounting.
"""

from sqlalchemy     import CheckConstraint, ForeignKey, Numeric, Enum as SqlEnum
from uuid           import UUID
from sqlalchemy.orm import Mapped, mapped_column
from decimal        import Decimal
from app.db.base    import Base
from app.db.enums   import TransactionReferenceType

class CapitalLot(Base):
    """
    FIFO principal capital lot.
    """

    __tablename__ = "capital_lots"

    __table_args__ = (
        CheckConstraint(
            "original_amount > 0",
            name="ck_capital_lots_original_positive"
        ),
        CheckConstraint(
            """
            remaining_amount >=0 AND remaining_amount <= original_amount
            """,
            name="ck_capital_lots_remaining_valid"
        )
    )

    id                   : Mapped[UUID]                     = mapped_column(primary_key=True)
    user_id              : Mapped[UUID]                     = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    source_reference_id  : Mapped[UUID]                     = mapped_column(nullable=False)
    source_reference_type: Mapped[TransactionReferenceType] = mapped_column(SqlEnum(TransactionReferenceType, name="ledger_reference_type", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    original_amount      : Mapped[Decimal]                  = mapped_column(Numeric(20, 8), nullable=False)
    remaining_amount     : Mapped[Decimal]                  = mapped_column(Numeric(20, 8), nullable=False)
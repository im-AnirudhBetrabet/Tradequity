"""
Capital lot repository
"""

from uuid    import UUID, uuid4
from decimal import Decimal

from app.db.models.capital_lot import CapitalLot
from app.db.enums              import TransactionReferenceType
from sqlalchemy.ext.asyncio    import AsyncSession
class CapitalLotRepository:
    """
    Capital lot persistence access layer.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deposit_lot(self, user_id: UUID, source_reference_id: UUID, amount: Decimal):
        lot = CapitalLot(
            id=uuid4(),
            user_id=user_id,
            source_reference_id=source_reference_id,
            source_reference_type=TransactionReferenceType.DEPOSIT,
            original_amount=amount,
            remaining_amount=amount
        )

        self.db.add(lot)

        await self.db.flush()

        return lot
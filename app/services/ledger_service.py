"""
Ledger business services.

This module contains business workflows for financial
ledger operations.
"""

from decimal import Decimal
from uuid    import uuid4

from app.core.exceptions  import ResourceNotFoundError
from app.db.models.ledger import LedgerTransaction
from app.db.enums         import TransactionReferenceType

from sqlalchemy.ext.asyncio                  import AsyncSession
from app.repositories.capital_lot_repository import CapitalLotRepository
from app.repositories.account_repository     import AccountRepository
from app.repositories.ledger_repository      import LedgerRepository
from app.repositories.profile_repository     import ProfileRepository
from app.schemas.admin.ledger                import AdminDepositRequest, AdminDepositResponse

class LedgerService:
    """
    Financial ledger application service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

        self.capital_lot_repository = CapitalLotRepository(db)
        self.account_repository     = AccountRepository(db)
        self.ledger_repository      = LedgerRepository(db)
        self.profile_repository     = ProfileRepository(db)

    async def record_deposit(self, request: AdminDepositRequest) -> AdminDepositResponse:
        """
        Record investment deposit

        Workflow:
            - validate investor
            - locate user cash account
            - create immutable ledger transaction
            - create FIFO capital lot
            - return updated balance

        Args:
            request:
                Administrative deposit request.

        Returns:
            AdminDepositResponse:
                Deposit confirmation payload.
        """
        try:
            profile = await self.profile_repository.get_active_by_id(request.user_id)

            if profile is None:
                raise ResourceNotFoundError("Investor profile not found")

            cash_account = await self.account_repository.get_user_cash_account(request.user_id)

            if cash_account is None:
                raise ResourceNotFoundError("User cash account not found")

            transaction = LedgerTransaction(
                id=uuid4(),
                from_account_id=None,
                to_account_id=cash_account.id,
                amount=request.amount,
                reference_type=TransactionReferenceType.DEPOSIT,
                ledger_metadata={
                    "payment_method": request.payment_method,
                    "payment_reference": request.payment_reference
                }
            )

            await self.ledger_repository.create(transaction)

            await self.capital_lot_repository.create_deposit_lot(
                user_id=request.user_id,
                source_reference_id=transaction.id,
                amount=request.amount
            )

            updated_balance = await self.ledger_repository.get_account_balance(cash_account.id)

            await self.db.commit()
            return AdminDepositResponse(
                transaction_id=transaction.id,
                user_id=request.user_id,
                amount=request.amount,
                updated_cash_balance=updated_balance
            )
        except Exception:
            await self.db.rollback()
            raise


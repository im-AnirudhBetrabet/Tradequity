"""
Pooled buy execution business service.

This module implements the administrative pooled buy workflow for Tradequity.

Workflow responsibilities:
    - Validate allocation instructions.
    - Validate user existence and account balances.
    - Record trade execution.
    - Create pooled master position.
    - Derive beneficial ownership allocations.
    - Record capital movement in the ledger.
    - Return workflow response payload.

Design principles:
    - Atomic transactional execution.
    - Explicit business validation.
    - Repository-backed persistence access.
    - Exact decimal financial calculations.
"""

from decimal import Decimal, ROUND_DOWN
from uuid    import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions    import InsufficientFundsError, InvalidAllocationError, ResourceNotFoundError
from app.db.enums           import AllocationStatus, PositionStatus, TradeType, TransactionReferenceType

from app.db.models.allocation import PositionAllocation
from app.db.models.ledger     import LedgerTransaction
from app.db.models.position   import MasterPosition
from app.db.models.trade      import TradeExecution
from app.repositories         import AccountRepository, AllocationRepository, LedgerRepository, PositionRepository, ProfileRepository, TradeRepository
from app.schemas.admin.trade  import AllocationInput, BuyTradeRequest, BuyTradeResponse, TradeExecutionResponse

_DECIMAL_PRECISION = Decimal("0.00000001")

class BuyService:
    """
    Administrative pooled buy execution service.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initializes service dependencies

        Args:
            db:
                Active asynchronous database session.
        """
        self.db                    = db
        self.profile_repository    = ProfileRepository(db)
        self.account_repository    = AccountRepository(db)
        self.ledger_repository     = LedgerRepository(db)
        self.trade_repository      = TradeRepository(db)
        self.position_repository   = PositionRepository(db)
        self.allocation_repository = AllocationRepository(db)


    async def execute_buy(self, request: BuyTradeRequest, admin_user_id: UUID) -> BuyTradeResponse:
        """
        Execute a pooled buy workflow
        Args:
            request:
                Administrative buy request payload.

            admin_user_id:
                Administrator actor executing the trade.

        Returns:
            BuyTradeResponse:
                Workflow execution summary.

        Raises:
            InvalidAllocationError:
                If allocation instructions are invalid.

            ResourceNotFoundError:
                If required users or platform accounts are missing.

            InsufficientFundsError:
                If user balances are insufficient.
        """
        async with self.db.begin():
            total_trade_cost = self._calculate_total_trade_cost(
                quantity= request.quantity,
                price   = request.price,
                charges = request.charges
            )

            self._validate_allocations(
                expected_total= total_trade_cost,
                allocations   = request.allocations
            )

            await self._validate_users_and_balances(
                allocations=request.allocations,
            )

            treasury_account = await self.account_repository.get_platform_treasury_account()

            if treasury_account is None:
                raise ResourceNotFoundError("Platform treasury account not configured")

            trade = await self._create_trade_execution(request=request, admin_user_id=admin_user_id)

            position = await self._create_master_position(
                request =request,
                trade_id=trade.id
            )

            trade.position_id = position.id

            await self.trade_repository.update(trade)

            allocation_records = self._build_position_allocations(
                total_trade_cost= total_trade_cost,
                position_id     = position.id,
                request         = request
            )

            await self.allocation_repository.create_many(allocation_records)

            ledger_transactions = await self._build_ledger_transactions(
                treasury_account_id= treasury_account.id,
                reference_id       = trade.id,
                allocations        = request.allocations
            )

            await self.ledger_repository.create_many(ledger_transactions)

            return BuyTradeResponse(
                trade=TradeExecutionResponse.model_validate(trade),
                position_id=position.id,
                total_allocated_amount=sum(
                    allocations.amount for allocations in request.allocations
                ),
                allocations_count=len(request.allocations)
            )

    def _calculate_total_trade_cost(self, quantity: Decimal, price: Decimal, charges: Decimal) -> Decimal:
        """
        Calculate total acquisition cost.

        Args:
            quantity:
                Trade quantity.

            price:
                Per-unit execution price.

            charges:
                Execution charges.

        Returns:
            Decimal:
                Total acquisition cost.
        """

        return (quantity * price + charges).quantize(_DECIMAL_PRECISION)

    def _validate_allocations(self, allocations: list[AllocationInput], expected_total: Decimal) -> None:
        """
        Validate allocation business rules.

        Args:
            allocations:
                Submitted allocation instructions.

            expected_total:
                Expected total allocation amount.


        Raises:
            InvalidAllocationError:
                If validation fails.
        """
        if not allocations:
            raise InvalidAllocationError("At least one allocation is required")

        user_ids = [allocation.user_id for allocation in allocations]

        if len(user_ids) != len(set(user_ids)):
            raise InvalidAllocationError("Duplication user allocations are not allowed.")

        actual_total = sum( allocation.amount for allocation in allocations ).quantize(_DECIMAL_PRECISION)

        if actual_total != expected_total:
            raise InvalidAllocationError("Allocation total must exactly match trade cost")

    async def _validate_users_and_balances(self, allocations: list[AllocationInput]) -> None:
        """
        Validate user existence and funding capacity.

        Args:
            allocations:
                Allocation instructions

        Raises:
            ResourceNotFoundError:
                If required users or accounts are missing.

            InsufficientFundsError:
                If balances are insufficient.
        """
        for allocation in allocations:
            profile = await self.profile_repository.get_active_by_id(allocation.user_id)

            if profile is None:
                raise ResourceNotFoundError(f"User not found: {allocation.user_id}")

            cash_account = await self.account_repository.get_user_cash_account(allocation.user_id)

            if cash_account is None:
                raise ResourceNotFoundError(f"Cash account missing for user: {allocation.user_id}")

            balance = await self.ledger_repository.get_account_balance(cash_account.id)

            if balance < allocation.amount:
                raise InsufficientFundsError(f"Insufficient funds for user: {allocation.user_id}")

    async def _create_trade_execution(self, request: BuyTradeRequest, admin_user_id: UUID) -> TradeExecution:
        """
        Create a trade execution record
        Args:
            request:
                Buy request payload.

            admin_user_id:
                Administrative actor identifier.

        Returns:
            TradeExecution:
                Persisted trade execution.
        """
        trade = TradeExecution(
            id=uuid4(),
            trade_type=TradeType.BUY,
            symbol=request.symbol,
            instrument_name=request.instrument_name,
            asset_type=request.asset_type,
            position_id=None,
            quantity=request.quantity,
            price=request.price,
            charges=request.charges,
            executed_at=request.executed_at,
            entered_by=admin_user_id,
            notes=request.notes
        )

        return await self.trade_repository.create(trade)

    async def _create_master_position(self, request: BuyTradeRequest, trade_id: UUID) -> MasterPosition:
        """
        Create pooled master position.

        Args:
            request:
                Buy request payload.

            trade_id:
                Originating trade identifier.

        Returns:
            MasterPosition:
                Persisted master position.
        """
        position = MasterPosition(
            id=uuid4(),
            originating_trade_id=trade_id,
            symbol=request.symbol,
            instrument_name=request.instrument_name,
            asset_type=request.asset_type,
            total_quantity=request.quantity,
            remaining_quantity=request.quantity,
            status=PositionStatus.OPEN,
            opened_at=request.executed_at,
            closed_at=None,
        )

        return await self.position_repository.create(position)
    
    def _build_position_allocations(self, request: BuyTradeRequest, position_id: UUID, total_trade_cost: Decimal) -> list[PositionAllocation]:
        """
        Build user beneficial ownership allocations.

        Args:
            request:
                Buy request payload.

            position_id:
                Target acquisition cost.

        Returns:
            list[PositionAllocation]:
                Allocation entities.
        """
        effective_unit_cost = (total_trade_cost / request.quantity).quantize(_DECIMAL_PRECISION)

        allocations: list[PositionAllocation] = []
        allocated_quantity_total              = Decimal("0")

        for index, allocation in enumerate(request.allocations):
            is_last = index == len(request.allocations) - 1

            if is_last:
                allocation_quantity = (request.quantity - allocated_quantity_total).quantize(_DECIMAL_PRECISION)

            else:
                allocation_quantity = (allocation.amount / effective_unit_cost).quantize(_DECIMAL_PRECISION, rounding=ROUND_DOWN)

                allocated_quantity_total += allocation_quantity

            allocations.append(
                PositionAllocation(
                    id=uuid4(),
                    user_id=allocation.user_id,
                    position_id=position_id,
                    original_quantity=allocation_quantity,
                    remaining_quantity=allocation_quantity,
                    original_cost=allocation.amount,
                    remaining_cost=allocation.amount,
                    status=AllocationStatus.OPEN,
                    opened_at=request.executed_at,
                    closed_at=None
                )
            )
        return allocations

    async def _build_ledger_transactions(self, allocations: list[AllocationInput], treasury_account_id: UUID, reference_id: UUID) -> list[LedgerTransaction]:
        """
        Build ledger movement entries.

        Args:
            allocations:
                Allocation instructions.

            treasury_account_id:
                Platform treasury account identifier.

            reference_id:
                Trade reference identifier.

        Returns:
            list[LedgerTransaction]:
                Ledger entries.
        """
        transactions: list[LedgerTransaction] = []

        for allocation in allocations:
            cash_account = await self.account_repository.get_user_cash_account(allocation.user_id)

            if cash_account is None:
                raise ResourceNotFoundError(f"Cash account missing for user: {allocation.user_id}")

            transactions.append(
                LedgerTransaction(
                    id=uuid4(),
                    from_account_id=cash_account.id,
                    to_account_id=treasury_account_id,
                    amount=allocation.amount,
                    reference_type=TransactionReferenceType.ALLOCATION,
                    reference_id=reference_id,
                    description=f"Capital allocation for pooled buy trade {reference_id}"
                )
            )

        return transactions
"""
Administrative buy execution business service.

Whole-share allocation model:
    - Admin explicitly assigns whole shares per user.
    - Backend computes per-user cost.
    - Charges allocated proportionally by share count.
    - Full trade executes atomically or fails entirely.
"""

from decimal import Decimal
from http.client import responses
from uuid    import UUID, uuid4

from app.core.exceptions import InsufficientFundsError, InvalidAllocationError, ResourceNotFoundError
from app.db.enums        import AllocationStatus, PositionStatus, TradeType, TransactionReferenceType

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MasterPosition
from app.db.models.allocation import PositionAllocation
from app.db.models.ledger     import LedgerTransaction
from app.db.models.trade      import TradeExecution
from app.repositories         import AccountRepository, AllocationRepository, LedgerRepository, PositionRepository, ProfileRepository, TradeRepository
from app.schemas.admin.trade  import AllocationInput, BuyTradeRequest, BuyTradeResponse, TradeExecutionResponse

class BuyService:
    """
    Administrative whole-share buy execution service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

        self.account_repository    = AccountRepository(db)
        self.allocation_repository = AllocationRepository(db)
        self.ledger_repository     = LedgerRepository(db)
        self.position_repository   = PositionRepository(db)
        self.profile_repository    = ProfileRepository(db)
        self.trade_repository      = TradeRepository(db)
        self._DECIMAL_PRECISION    = Decimal("0.00000001")

    async def execute_buy(self, request: BuyTradeRequest, admin_user_id: UUID) -> BuyTradeResponse:
        """
        Execute buy workflow atomically.

        Rules:
            - exact whole-share allocations only.
            - charges split proportionally.
            - insufficient funds for any user rejects full trade.
        """
        try:
            self._validate_allocations(request.allocations)

            total_trade_cost = self._validate_total_trade_cost(
                quantity= request.quantity,
                price   = request.price,
                charges = request.charges
            )

            user_costs           = self._calculate_user_costs(request)
            locked_cash_accounts = await self._validate_users_and_balances(user_costs=user_costs)
            treasury_account     = await self.account_repository.get_platform_treasury_account()

            if treasury_account is None:
                raise ResourceNotFoundError("Platform treasury account not configured")

            trade = await self._create_trade_execution(request=request, admin_user_id=admin_user_id)

            position = await self._create_master_position(
                request=request,
                trade_id=trade.id,
                total_trade_cost=total_trade_cost
            )

            allocation_records = self._build_position_allocations(
                request=request,
                position_id=position.id,
                user_costs=user_costs
            )

            await self.allocation_repository.create_many(allocation_records)

            ledger_transactions = self._build_ledger_transactions(
                allocations=request.allocations,
                treasury_account_id=treasury_account.id,
                reference_id=trade.id,
                locked_cash_accounts=locked_cash_accounts,
                user_costs=user_costs
            )
            await self.ledger_repository.create_many(ledger_transactions)

            response = BuyTradeResponse(
                trade=TradeExecutionResponse.model_validate(trade),
                position_id=position.id,
                total_allocated_quantity=request.quantity,
                allocation_count=len(request.allocations)
            )

            await self.db.commit()
            return response

        except Exception:
            await self.db.rollback()
            raise

    def _validate_allocations(self, allocations: list[AllocationInput]) -> None:
        """
        Validate allocation business rules

        Args:
            allocations:
                The list of allocations being executed
        Raises:
            InvalidAllocationError
                If allocation business rules are not met.
        """

        if not allocations:
            raise InvalidAllocationError("At least one allocation is required")

        user_ids = [allocation.user_id for allocation in allocations]

        if len(user_ids) != len(set(user_ids)):
            raise InvalidAllocationError("Duplicate user allocations are not allowed")

        return

    def _validate_total_trade_cost(self, quantity: Decimal, price: Decimal, charges: Decimal) -> Decimal:
        """
        Calculate total trade acquisition cost.

        Args:
            quantity:
                Total shares purchased.

            price:
                Price per share.

            charges:
                Total transactional charges.

        Returns:
             Decimal:
                Total trade cost.
        """
        return (quantity * price + charges).quantize(self._DECIMAL_PRECISION)

    def _calculate_user_costs(self, request: BuyTradeRequest) -> dict[UUID, Decimal]:
        """
        Calculate exact per-user trade cost.

        Charges are allocated proportionally by share count.
        Final user absorbs rounding remainder.
        """

        user_costs : dict[UUID, Decimal] = {}

        remaining_charges = request.charges
        allocations       = request.allocations

        for index, allocation in enumerate(allocations):
            base_cost = (allocation.quantity * request.price).quantize(self._DECIMAL_PRECISION)

            is_last = index == len(allocations) - 1

            if is_last:
                charge_share = remaining_charges
            else:
                share_ratio  = allocation.quantity / request.quantity

                charge_share = (request.charges * share_ratio).quantize(self._DECIMAL_PRECISION)

                remaining_charges -= charge_share

            total_cost = (base_cost + charge_share).quantize(self._DECIMAL_PRECISION)

            user_costs[allocation.user_id] = total_cost

        return user_costs

    async def _validate_users_and_balances(self, user_costs: dict[UUID, Decimal]) -> dict[UUID, UUID]:
        """
        Validate user existence and available funding.

        Locks cash accounts deterministically.
        """

        locked_cash_accounts: dict[UUID, UUID] = {}

        sorted_user_ids = sorted(user_costs.keys(), key= lambda user_id: str(user_id))

        for user_id in sorted_user_ids:
            required_amount = user_costs[user_id]

            profile = await self.profile_repository.get_active_by_id(user_id)

            if profile is None:
                raise ResourceNotFoundError(f"User not found: {user_id}")

            cash_account = await self.account_repository.get_user_cash_account_for_update(user_id)

            if cash_account is None:
                raise ResourceNotFoundError(f"Cash account missing for user: {user_id}")

            balance = await self.ledger_repository.get_account_balance(cash_account.id)

            if balance < required_amount:
                raise InsufficientFundsError(f"Insufficient funds for user: {user_id}")

            locked_cash_accounts[user_id] = cash_account.id

        return locked_cash_accounts

    async def _create_trade_execution(self, request: BuyTradeRequest, admin_user_id: UUID) -> TradeExecution:
        """
        Create trade execution record.

        Args:
            request:
                Trade Buy request.

            admin_user_id:
                Administrator actor identifier

        Return:
            TradeExecution:
                Trade execution record.
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

    async def _create_master_position(self, request: BuyTradeRequest, trade_id: UUID, total_trade_cost: Decimal) -> MasterPosition:
        """
        Create master position

        Args:
            request:
                Trade Buy request.

            trade_id:
                Trade buy record identifier.

            total_trade_cost:
                Total cost incurred for executing the trade.

        Returns:
             MasterPosition:
                New master position created for the trade.
        """

        position = MasterPosition(
            id=uuid4(),
            originating_trade_id=trade_id,
            symbol=request.symbol,
            instrument_name=request.instrument_name,
            asset_type=request.asset_type,
            total_quantity=request.quantity,
            remaining_quantity=request.quantity,
            allocated_quantity=Decimal("0"),
            buy_price=request.price,
            total_cost=total_trade_cost,
            status=PositionStatus.OPEN,
            opened_at=request.executed_at,
            closed_at=None
        )

        return await self.position_repository.create(position)

    def _build_position_allocations(self, request: BuyTradeRequest, position_id: UUID, user_costs: dict[UUID, Decimal]) -> list[PositionAllocation]:
        """
        Build whole share ownership allocations.

        Args:
             request:
                Trade Buy request.

            position_id:
                Referencing master position id.

            user_costs:
                Map of transaction charges distributed across participating users.

        Returns:
            list[PositionAllocations]:
                List of position allocations for participating users.
        """

        allocations: list[PositionAllocation] = []

        for allocation in request.allocations:
            allocations.append(
                PositionAllocation(
                    id=uuid4(),
                    user_id=allocation.user_id,
                    position_id=position_id,
                    original_quantity=allocation.quantity,
                    remaining_quantity=allocation.quantity,
                    original_cost=user_costs[allocation.user_id],
                    remaining_cost=user_costs[allocation.user_id],
                    status=AllocationStatus.OPEN,
                    opened_at=request.executed_at,
                    closed_at=None,
                )
            )

        return allocations

    def _build_ledger_transactions(self, allocations: list[AllocationInput], treasury_account_id: UUID, reference_id: UUID, locked_cash_accounts: dict[UUID, UUID], user_costs: dict[UUID, Decimal]) -> list[LedgerTransaction]:
        """
        Build funding ledger transactions
        Args:
            allocations:
                List of allocations made for participating users.

            treasury_account_id:
                Identifier for the platform treasury account.

            reference_id:

            locked_cash_accounts:
                Map of user_ids to their respective cash accounts.

            user_costs:
                Map of transactions cost shares to participating member ids.

        Returns:
            list[LedgerTransactions]:
                List of ledger transactions for the trade.
        """
        transactions: list[LedgerTransaction] = []

        for allocation in allocations:
            cash_account_id = locked_cash_accounts.get(
                allocation.user_id
            )

            if cash_account_id is None:
                raise ResourceNotFoundError(
                    f"Cash account missing for user: {allocation.user_id}"
                )

            transactions.append(
                LedgerTransaction(
                    id=uuid4(),
                    from_account_id=cash_account_id,
                    to_account_id=treasury_account_id,
                    amount=user_costs[allocation.user_id],
                    reference_type=TransactionReferenceType.ALLOCATION,
                    reference_id=reference_id,
                    ledger_metadata={
                        "event": "buy_allocation",
                        "trade_id": str(reference_id),
                        "user_id": str(allocation.user_id),
                        "quantity": str(allocation.quantity),
                    },
                )
            )

        return transactions
"""
Pooled sell execution service.

This module implements pooled investment sell workflow including
proportional liquidation and targeted investor liquidation.

Design principles:
    - Transaction - safe financial state mutation.
    - Deterministic locking.
    - Immutable financial event creation.
    - Clear separation between orchestration and accounting logic.
"""

from decimal import Decimal
from uuid    import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config     import settings
from app.core.exceptions import ResourceNotFoundError, SellValidationError
from app.db.enums        import SellMode, TradeType, TransactionReferenceType, PositionStatus, AllocationStatus
from app.db.models import AllocationRealization, LedgerTransaction, TradeExecution, Profile

from app.repositories.account_repository     import AccountRepository
from app.repositories.allocation_repository  import AllocationRepository
from app.repositories.ledger_repository      import LedgerRepository
from app.repositories.position_repository    import PositionRepository
from app.repositories.realization_repository import RealizationRepository
from app.repositories.trade_repository       import TradeRepository
from app.repositories.profile_repository     import ProfileRepository

from app.schemas.admin.trade import SellTradeRequest, SellTradeResponse, TradeExecutionResponse

class SellService:
    """
    Service for pooled sell execution workflows.
    """

    EPSILON = Decimal("0.00000001")

    def __init__(self, db: AsyncSession) -> None:
        """
        Initializes service dependencies.

        Args:
             db:
                Active asynchronous database session.
        """
        self.db = db

        self.account_repository     = AccountRepository(db)
        self.allocation_repository  = AllocationRepository(db)
        self.ledger_repository      = LedgerRepository(db)
        self.position_repository    = PositionRepository(db)
        self.realization_repository = RealizationRepository(db)
        self.trade_repository       = TradeRepository(db)
        self.profile_repository     = ProfileRepository(db)
        self._performance_fee_rate  = settings.platform_performance_fee

    async def execute_sell(self, request: SellTradeRequest, admin_user_id: UUID) -> SellTradeResponse:
        """
        Execute pooled sell workflow.

        Supports:
            - proportional pooled liquidation.
            - targeted investor liquidation.

        Args:
            request:
                Administrative sell request payload.

            admin_user_id:
                Administrative actor executing the sell.

        Returns:
            SellTradeResponse:
                Sell execution summary.
        """
        try:
            position = await self._validate_and_lock_position(request.position_id)

            allocations = await self._select_and_lock_allocations(request=request, position_id=position.id)

            self._validate_sell_quantity(request=request, allocations=allocations, position=position)

            sell_trade = await self._create_sell_trade(request=request, admin_user_id=admin_user_id, position_id=position.id, position=position)

            realizations = await self._build_realizations(
                request=request,
                sell_trade=sell_trade,
                allocations=allocations,
            )

            await self.realization_repository.create_many(realizations)

            ledger_transactions = await self._build_ledger_transactions(
                realizations=realizations,
                allocations=allocations,
            )

            await self.ledger_repository.create_many(ledger_transactions)

            await self._apply_allocation_updates(
                allocations=allocations,
                realizations=realizations,
                executed_at=request.executed_at,
            )

            await self._apply_position_update(
                position=position,
                sell_quantity=request.quantity,
                executed_at=request.executed_at,
            )

            response = SellTradeResponse(
                trade=TradeExecutionResponse.model_validate(sell_trade),
                realized_allocations=len(realizations),
                total_net_credit=sum(realization.net_credit for realization in realizations),
                total_fee_collected=sum(realization.performance_fee for realization in realizations)
            )

            await self.db.commit()

            return response

        except Exception:
            await self.db.rollback()
            raise

    async def _validate_and_lock_position(self, position_id: UUID):
        """
        Validate and lock target master position.

        Args:
            position_id:
                Target master position identifier.

        Returns:
            MasterPosition:
                Locked open position.

        Raises:
            ResourceNotFoundError:
                If position does not exist.

            SellValidationError:
                If position is not open.
        """

        position = await self.position_repository.get_by_id_for_update(position_id)

        if position is None:
            raise ResourceNotFoundError(f"Position not found: {position_id}")

        if position.status != PositionStatus.OPEN:
            raise SellValidationError("Position is not open for liquidation")

        if position.remaining_quantity <= self.EPSILON:
            raise SellValidationError("Position has no remaining quantity")

        return position

    async def _select_and_lock_allocations(self, request: SellTradeRequest, position_id: UUID):
        """
        Select and lock participating allocations.

        Args:
            request:
                Sell request payload.

            position_id:
                Target master position identifier.

        Returns:
            list[PositionAllocation]:
                Locked participating allocations.

        Raises:
            SellValidationError:
                If no matching allocations exist.
        """

        if request.mode == SellMode.PROPORTIONAL:
            allocations = await self.allocation_repository.get_open_by_position_id_for_update(position_id=position_id)
        else:
            allocations = await self.allocation_repository.get_open_by_position_and_user_for_update(position_id=position_id, user_id=request.target_user_id)

        if not allocations:
            raise SellValidationError("No eligible allocations found")

        return allocations

    def _validate_sell_quantity(self, request: SellTradeRequest, allocations, position) -> None:
        """
        Validate requested sell quantity.

        Args:
            request:
                Sell request payload.

            allocations:
                Participating allocations.

            position:
                Locked master position.

        Raises:
             SellValidationError:
                If requested quantity exceeds available quantity.
        """

        if request.quantity > position.remaining_quantity:
            raise SellValidationError("Requested sell quantity exceeds position holdings")

        allocation_total = sum( allocation.remaining_quantity for allocation in allocations )

        if request.mode == SellMode.TARGETED:
            if request.quantity > allocation_total:
                raise SellValidationError("Requested sell quantity exceeds target user's holdings")

        if allocation_total <= self.EPSILON:
            raise SellValidationError("No sellable allocation quantity available")

        return

    async def _create_sell_trade(self, request: SellTradeRequest, admin_user_id: UUID, position_id: UUID, position):
        """
        Create immutable sell trade execution record

        Args:
            request:
                Sell request payload.

            admin_user_id:
                Administrative actor.

            position_id:
                Target master position identifier.

            position:
                Locked master position.

        Returns:
            TradeExecution:
                Persisted sell trade record.
        """

        trade = TradeExecution(
            id=uuid4(),
            trade_type=TradeType.SELL,
            symbol=position.symbol,
            instrument_name=position.instrument_name,
            asset_type=position.asset_type,
            position_id=position_id,
            quantity=request.quantity,
            price=request.price,
            charges=request.charges,
            executed_at=request.executed_at,
            entered_by=admin_user_id,
            notes=request.notes
        )

        return await self.trade_repository.create(trade)

    async def _build_realizations(self, request: SellTradeRequest, sell_trade, allocations):
        """
        Build allocation realization records.

        Args:
            request:
                Sell request payload.

            sell_trade:
                Persisted sell trade.

            allocations:
                Participating allocations

        Returns:
            list[AllocationRealization]:
                Realization records.
        """


        total_selected_quantity = sum(
            allocation.remaining_quantity
            for allocation in allocations
        )

        user_profiles: dict[UUID, Profile] = {}

        for allocation in allocations:
            if allocation.user_id not in user_profiles:
                profile = await self.profile_repository.get_by_id(allocation.user_id)

                if profile is None:
                    raise ResourceNotFoundError(f"Profile not found: {allocation.user_id}")

                user_profiles[allocation.user_id] = profile

        realizations = []

        for allocation in allocations:
            profile      = user_profiles[allocation.user_id]
            share_ratio  = allocation.remaining_quantity / total_selected_quantity

            realized_quantity = request.quantity * share_ratio

            cost_per_unit = allocation.remaining_cost / allocation.remaining_quantity

            realized_cost = realized_quantity * cost_per_unit

            gross_proceeds = realized_quantity *  request.price

            charge_share = request.charges * share_ratio

            realized_pnl = gross_proceeds - realized_cost - charge_share

            if realized_pnl > Decimal("0") and realized_cost > self.EPSILON:
                profit_pct = realized_pnl / realized_cost
                if profit_pct >= profile.minimum_profit_threshold:
                    performance_fee = realized_pnl * self._performance_fee_rate
                else:
                    performance_fee = Decimal("0")

            net_credit = gross_proceeds - charge_share - performance_fee

            realization = AllocationRealization(
                id=uuid4(),
                allocation_id=allocation.id,
                trade_execution_id=sell_trade.id,
                realized_quantity=realized_quantity,
                realized_cost=realized_cost,
                gross_proceeds=gross_proceeds,
                realized_pnl=realized_pnl,
                performance_fee=performance_fee,
                net_credit=net_credit,
                execution_price=request.price,
                realized_at=request.executed_at,
            )

            realizations.append(realization)

        return realizations


    async def _build_ledger_transactions(self, realizations, allocations):
        """
        Build settlement and performance fee ledger transactions

        Args:
            realizations:
                Allocation realization records.

            allocations:
                Participating allocations.

        Returns:
            list[LedgerTransaction]:
                Ledger transactions.
        """

        treasury_account = await self.account_repository.get_platform_treasury_account()

        fee_reserve_account = await self.account_repository.get_platform_fee_reserve_account()

        if treasury_account is None:
            raise ResourceNotFoundError(f"Platform treasury account not found")

        if fee_reserve_account is None:
            raise ResourceNotFoundError(f"Platform fee reserve account not found")

        allocation_map = {
            allocation.id: allocation
            for allocation in allocations
        }

        ledger_transactions = []

        for realization in realizations:
            allocation = allocation_map[realization.allocation_id]

            settlement_account = await self.account_repository.get_user_settlement_account(allocation.user_id)

            if settlement_account is None:
                raise ResourceNotFoundError(f"Settlement account missing for user {allocation.user_id}")

            settlement_txn = LedgerTransaction(
                id=uuid4(),
                from_account_id=treasury_account.id,
                to_account_id=settlement_account.id,
                amount=realization.net_credit,
                reference_type=TransactionReferenceType.REALIZATION,
                reference_id=realization.trade_execution_id,
                ledger_metadata={
                    "event": "sell_settlement_credit",
                    "allocation_id": str(realization.allocation_id),
                },
            )

            ledger_transactions.append(settlement_txn)

            if realization.performance_fee > self.EPSILON:
                fee_txn = LedgerTransaction(
                    id=uuid4(),
                    from_account_id=treasury_account.id,
                    to_account_id=fee_reserve_account.id,
                    amount=realization.performance_fee,
                    reference_type=TransactionReferenceType.FEE,
                    reference_id=realization.trade_execution_id,
                    ledger_metadata={
                        "event": "performance_fee_capture",
                        "allocation_id": str(realization.allocation_id),
                    },
                )

                ledger_transactions.append(fee_txn)

        return ledger_transactions

    async def _apply_allocation_updates(self, allocations, realizations, executed_at) -> None:
        """
        Apply allocation ownership state updates

        Args:
            allocations:
                Participating allocations.

            realizations:
                Realization records.

            executed_at:
                Sell execution timestamp.
        """
        realization_map = {
            realization.allocation_id:  realization
            for realization in realizations
        }

        for allocation in allocations:
            realization = realization_map.get(allocation.id)

            if realization is None:
                continue

            allocation.remaining_quantity = allocation.remaining_quantity - realization.realized_quantity

            allocation.remaining_cost = allocation.remaining_cost - realization.realized_cost

            if allocation.remaining_quantity <= self.EPSILON:
                allocation.remaining_quantity = Decimal("0")
                allocation.remaining_cost     = Decimal("0")
                allocation.status             = AllocationStatus.CLOSED
                allocation.closed_at          = executed_at

            await self.allocation_repository.update(allocation)

    async def _apply_position_update(self, position, sell_quantity: Decimal, executed_at) -> None:
        """
            Apply master position state updates.

            Args:
                position:
                    Locked master position.

                sell_quantity:
                    Executed sell quantity.

                executed_at:
                    Sell execution timestamp.
            """
        position.remaining_quantity = (
                position.remaining_quantity
                - sell_quantity
        )

        position.allocated_quantity = (
            position.allocated_quantity - sell_quantity
        )

        if position.remaining_quantity <= self.EPSILON:
            position.remaining_quantity = Decimal("0")
            position.status             = PositionStatus.CLOSED
            position.closed_at          = executed_at

        await self.position_repository.update(position)
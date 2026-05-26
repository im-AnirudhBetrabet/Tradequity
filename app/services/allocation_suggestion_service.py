from decimal import Decimal
from uuid    import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions          import ResourceNotFoundError
from app.repositories             import AccountRepository, LedgerRepository, ProfileRepository
from app.schemas.admin.allocation import AllocationSuggestionOption, AllocationSuggestionRequest, AllocationSuggestionResponse, SuggestedAllocation,SuggestionStrategy



class AllocationSuggestionService:
    """
    Advisory allocation suggestion service.

    Produces whole-share allocation suggestions
    without mutating any system state.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

        self._DECIMAL_PRECISION   = Decimal("0.00000001")
        self._CONSERVATIVE_FACTOR = Decimal("0.70")

        self.account_repository = AccountRepository(db)
        self.profile_repository = ProfileRepository(db)
        self.ledger_repository  = LedgerRepository(db)

    async def generate_suggestions(self, request: AllocationSuggestionRequest) -> AllocationSuggestionResponse:
        """
        Generate all strategy suggestions
        """
        candidate_balances = await self._get_candidate_balances(request.candidate_user_ids)

        options = [
            self._max_deployment(request=request, candidate_balances=candidate_balances),
            self._proportional(request=request  , candidate_balances=candidate_balances),
            self._balanced(request=request      , candidate_balances=candidate_balances),
            self._conservative(request=request  , candidate_balances=candidate_balances)
        ]
        return AllocationSuggestionResponse(
            symbol            = request.symbol,
            price             = request.price,
            requested_quantity= request.target_quantity,
            options           = options
        )

    async def _get_candidate_balances(self, candidate_user_ids: list[UUID]) -> dict[UUID, Decimal]:
        """
        Load validate user available cash balances.
        Args:
            candidate_user_ids:
                List of user id's
        Returns:
            dict[UUID, Decimal]:
                Map user users with their corresponding cash balances.
        """

        balances: dict[UUID, Decimal] = {}

        for user_id in candidate_user_ids:
            profile = await self.profile_repository.get_active_by_id(user_id)

            if profile is None:
                raise ResourceNotFoundError(f"User not found: {user_id}")

            cash_account = await self.account_repository.get_user_cash_account(user_id)

            if cash_account is None:
                raise ResourceNotFoundError(f"Cash account missing for user: {user_id}")

            balance = await self.ledger_repository.get_account_balance(cash_account.id)

            balances[user_id] = balance.quantize(self._DECIMAL_PRECISION)

        return balances

    def _estimate_cost(self, quantity: Decimal, total_quantity: Decimal, price: Decimal, estimated_charges: Decimal, is_last: bool=False, remaining_charges: Decimal | None = None) -> Decimal:
        """
        Estimate user allocation cost.
        Args:
            quantity:
                Quantity being allocated to the user

            total_quantity:
                Total quantity being purchased

            price:
                Per-unit price of the share being purchased

            estimated_charges:
                Approximate transaction charges.

            is_last:
                Boolean indicating if user is the last candidate in the allocation set.

            remaining_charges:
                Remaining transactions charges.

        Returns:
            Decimal:
                Estimated user allocation cost.
        """
        base_cost = (quantity * price).quantize(self._DECIMAL_PRECISION)

        if is_last and remaining_charges is not None:
            charge_share = remaining_charges
        else:
            charge_share = (estimated_charges * (quantity / total_quantity)).quantize(self._DECIMAL_PRECISION)

        return (base_cost + charge_share).quantize(self._DECIMAL_PRECISION)

    def _build_option(self, strategy: SuggestionStrategy, allocations: dict[UUID, Decimal], candidate_balances: dict[UUID, Decimal], request: AllocationSuggestionRequest) -> AllocationSuggestionOption:
        """
        Build response option payload

        Args:
            strategy:
                Allocation strategy being used

            allocations:
                Map of users to their share of stocks in the current trade according to the said strategy.

            candidate_balances:
                Map of users to their available cash balances.

            request:
                Trade allocation request

        :return:
            AllocationSuggestionResponse
        """
        suggestions      : list[SuggestedAllocation] = []
        remaining_charges: Decimal                   = request.estimated_charges
        items            : list[tuple[UUID, Decimal]]= list(allocations.items())

        for index, (user_id, quantity) in enumerate(items):
            is_last: bool = index == len(items) - 1

            estimated_cost = self._estimate_cost(
                quantity=quantity,
                total_quantity=request.target_quantity,
                price=request.price,
                estimated_charges=request.estimated_charges,
                is_last=is_last,
                remaining_charges=remaining_charges
            )

            if not is_last:
                proportional_charge = (
                    request.estimated_charges * (quantity / request.target_quantity).quantize(self._DECIMAL_PRECISION)
                )

                remaining_charges -= proportional_charge

            suggestions.append(
                SuggestedAllocation(
                    user_id=user_id,
                    quantity=quantity,
                    estimated_cost=estimated_cost,
                    available_cash=candidate_balances[user_id]
                )
            )

        achievable_quantity = sum(allocations.values())

        return AllocationSuggestionOption(
            strategy=strategy,
            achievable_quantity=achievable_quantity,
            allocations=suggestions
        )

    def _max_deployment(self, request: AllocationSuggestionRequest, candidate_balances: dict[UUID, Decimal]) -> AllocationSuggestionOption:
        """
        Largest-wallet-first greedy allocation

        Args:

            request:
                Trade Allocation request.

            candidate_balances:
                Map of users to their corresponding cash-balances

        Returns:
            AllocationSuggestionOption.
        :return:
        """
        sorted_users = sorted(candidate_balances.items(), key= lambda item: item[1], reverse=True)

        allocations: dict[UUID, Decimal] = {}
        remaining_target                 = request.target_quantity

        for user_id, balance in sorted_users:
            if remaining_target <= 0:
                break

            max_affordable = self._max_affordable_quantity(balance=balance, total_quantity=request.target_quantity, price=request.price, estimated_charges=request.estimated_charges, cap=remaining_target)

            if max_affordable <= 0:
                continue

            assigned = min(max_affordable, remaining_target)

            allocations[user_id] = assigned
            remaining_target    -= assigned

        return self._build_option(
            strategy=SuggestionStrategy.MAX_DEPLOYMENT,
            allocations=allocations,
            candidate_balances=candidate_balances,
            request=request
        )

    def _proportional(self, request: AllocationSuggestionRequest, candidate_balances: dict[UUID, Decimal]) -> AllocationSuggestionOption:
        """
        Wallet - proportional whole-share allocation
        Args:
            request:
                Trade allocation request

            candidate_balances:
                Map of users to their corresponding cash-balances.

        Returns:
            AllocationSuggestionOption
        """
        total_balance = sum(candidate_balances.values())

        if total_balance <= 0:
            return self._build_option(
                strategy=SuggestionStrategy.PROPORTIONAL,
                allocations={},
                candidate_balances=candidate_balances,
                request=request
            )

        remainders : list[tuple[UUID, Decimal]] = []
        floors     : dict[UUID, Decimal]        = {}

        allocated = Decimal("0")

        for user_id, balance in candidate_balances.items():
            ideal = (request.target_quantity * (balance / total_balance))

            floored   = ideal.to_integral_value(rounding="ROUND_DOWN")
            remainder = ideal - floored

            floors[user_id] = floored
            remainders.append((user_id, remainder))

            allocated += floored

        remaining = request.target_quantity - allocated

        remainders.sort(
            key=lambda item: item[1],
            reverse=True
        )

        for user_id, _ in remainders:
            if remaining <=0:
                break
            floors[user_id] += Decimal("1")
            remaining       -= Decimal("1")

        valid_allocations: dict[UUID, Decimal] = {}

        for user_id, qty in floors.items():
            if qty <= 0:
                continue

            if self._can_afford(
                balance=candidate_balances[user_id],
                quantity=qty,
                total_quantity=request.target_quantity,
                price=request.price,
                estimated_charges=request.estimated_charges,
            ):
                valid_allocations[user_id] = qty

        return self._build_option(
            strategy=SuggestionStrategy.PROPORTIONAL,
            allocations=valid_allocations,
            candidate_balances=candidate_balances,
            request=request
        )

    def _balanced(self, request: AllocationSuggestionRequest, candidate_balances: dict[UUID, Decimal]) -> AllocationSuggestionOption:
        """
        Near-even distribution

        Args:

            request:
                Trade Allocation request.

            candidate_balances:
                Map of users to their corresponding cash-balances

        Returns:
            AllocationSuggestionOption.
        """
        user_ids = list(candidate_balances.keys())

        if not user_ids:
            return self._build_option(
                strategy=SuggestionStrategy.BALANCED,
                allocations={},
                candidate_balances=candidate_balances,
                request=request,
            )

        equal_share = (
            request.target_quantity / Decimal(len(user_ids))
        ).to_integral_value(rounding="ROUND_DOWN")

        allocations: dict[UUID, Decimal] = {}
        remaining = request.target_quantity

        for user_id in user_ids:
            if remaining <= 0:
                break

            max_affordable = self._max_affordable_quantity(
                balance=candidate_balances[user_id],
                total_quantity=request.target_quantity,
                price=request.price,
                estimated_charges=request.estimated_charges,
                cap=equal_share
            )

            assigned = min(equal_share, max_affordable, remaining)

            if assigned > 0:
                allocations[user_id] = assigned
                remaining           -= assigned

        return self._build_option(
            strategy=SuggestionStrategy.BALANCED,
            allocations=allocations,
            candidate_balances=candidate_balances,
            request=request
        )

    def _conservative(self, request: AllocationSuggestionRequest, candidate_balances: dict[UUID, Decimal]) -> AllocationSuggestionOption:
        """
        Intentionally under-deployed allocation

        Args:
            request:
                Trade Allocation request.

            candidate_balances:
                Map of users to their corresponding cash-balances

        Returns:
            AllocationSuggestionOption.
        """
        reduced_target = (request.target_quantity * self._CONSERVATIVE_FACTOR).to_integral_value(rounding="ROUND_DOWN")

        conservative_request = AllocationSuggestionRequest(
            symbol=request.symbol,
            price=request.price,
            estimated_charges=request.estimated_charges,
            target_quantity=max(reduced_target, Decimal("1")),
            candidate_user_ids=request.candidate_user_ids
        )
        option= self._balanced(request=conservative_request, candidate_balances=candidate_balances)

        option.strategy = SuggestionStrategy.CONSERVATIVE

        return option

    def _can_afford(self, balance: Decimal, quantity: Decimal, total_quantity, price: Decimal, estimated_charges: Decimal) -> bool:
        """
        Determine whether a user can afford an allocation
        including proportional charges.

        Args:
            balance:
                Users available cash-balance

            quantity:
                Quantity of shares being allocated to the users.

            total_quantity:
                Total quantity of shares being purchased.

            price:
                Price per share

            estimated_charges:
                Estimated charge for the purchase
        :return:
            bool:
                If the user can 'afford' the purchase
        """
        if quantity <= 0:
            return False

        estimated_cost = self._estimate_cost(
            quantity=quantity,
            total_quantity=total_quantity,
            price=price,
            estimated_charges=estimated_charges
        )

        return estimated_cost <= balance



    def _max_affordable_quantity(self, balance: Decimal, total_quantity: Decimal, price: Decimal, estimated_charges: Decimal, cap: Decimal) -> Decimal:
        """
        Find the highest affordable whole-share quantity
        including estimated charges.
        Args:
            balance:
                Users available cash balance.
            total_quantity:
                Total quantity being purchased.
            price:
                Price per share
            estimated_charges:
                Estimated charge for the purchase.
            cap:
        Return:
            Decimal:
        """
        candidate = cap

        while candidate > 0:
            if self._can_afford(balance=balance, quantity=candidate, total_quantity=total_quantity, price=price, estimated_charges=estimated_charges):
                return candidate

            candidate -= Decimal("1")

        return Decimal("0")
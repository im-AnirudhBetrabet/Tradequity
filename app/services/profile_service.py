"""
Profile business services.

This module contains application workflows related to
user profile operations.
"""
from math import ceil
from uuid import UUID

from app.core.exceptions                    import ResourceNotFoundError
from app.schemas.user.profile               import CurrentUserResponse, UpdateProfileRequest
from sqlalchemy.ext.asyncio                 import AsyncSession
from app.repositories.profile_repository    import ProfileRepository
from app.repositories.ledger_repository     import LedgerRepository
from app.repositories.account_repository    import AccountRepository
from app.repositories.allocation_repository import AllocationRepository
from app.repositories.position_repository   import PositionRepository
from app.schemas.admin.user import AdminInvestorSummaryResponse, PaginatedInvestorResponse, InvestorDetailResponse, \
    InvestorTransactionResponse, InvestorProfileResponse, InvestorSummaryResponse, InvestorHoldingResponse
from decimal                                import Decimal

class ProfileService:
    """
    Profile application service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.profile_repository    = ProfileRepository(db)
        self.account_repository    = AccountRepository(db)
        self.ledger_repository     = LedgerRepository(db)
        self.allocation_repository = AllocationRepository(db)
        self.position_repository   = PositionRepository(db)

    async def get_current_user_profile(self, user_id: UUID) -> CurrentUserResponse:
        """
        Retrieve the active application profile
        for the authenticated user.

        Args:
            user_id:
                Authenticated application user identifier.

        Returns:
            CurrentUserResponse:
                Authenticated user profile payload.

        Raises:
            ResourceNotFoundError:
                If no active profile exists.
        """

        profile = await self.profile_repository.get_active_by_id(user_id)

        if profile is None:
            raise ResourceNotFoundError("User profile not found")

        return CurrentUserResponse(
            id=profile.id,
            full_name=profile.full_name,
            role=profile.role,
            is_active=profile.is_active,
            minimum_profit_threshold=profile.minimum_profit_threshold,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    async def update_current_user_profile(self, user_id: UUID, request: UpdateProfileRequest) -> CurrentUserResponse:
        """
        Update authenticated user profile
        Args:
            user_id:
                Authenticated user identifier.

            request:
                Update payload

        Returns:
            ProfileResponse:
                Updated profile payload.

        Raises:
            ResourceNotFoundError:
                If profile does not exist.
        """

        profile = await self.profile_repository.update_full_name(user_id=user_id, full_name=request.full_name.strip())

        if profile is None:
            raise ResourceNotFoundError("User profile not found")

        return CurrentUserResponse(
            id=profile.id,
            full_name=profile.full_name,
            role=profile.role,
            is_active=profile.is_active,
            minimum_profit_threshold=profile.minimum_profit_threshold,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    async def list_investors(self, page: int, page_size: int, search: str | None) -> PaginatedInvestorResponse:
        """
        Retrieve Investor Response

        Args:
            page:
                Requested page number.

            page_size:
                Requested page size.

            search:
                Optional investor search

        Returns:
            PaginatedInvestorResponse
        """
        profiles, total = await self.profile_repository.search_investors(page=page, page_size=page_size, search=search)

        items = []

        holding_counts = await self.allocation_repository.get_active_position_counts([user.id for user in profiles])

        for profile in profiles:
            balance = Decimal("0")

            cash_account = await self.account_repository.get_user_cash_account(profile.id)

            if cash_account:
                balance = await self.ledger_repository.get_account_balance(cash_account.id)

            items.append(
                AdminInvestorSummaryResponse(
                    id=profile.id,
                    full_name=profile.full_name,
                    role=profile.role,
                    is_active=profile.is_active,
                    deployable_cash_balance=balance,
                    created_at=profile.created_at,
                    active_position_count=holding_counts.get(profile.id, 0)
                )
            )

        return PaginatedInvestorResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(
            ceil(total / page_size)
            if total > 0
            else 1
        ),
    )

    async def get_investor_details(self, user_id: UUID) -> InvestorDetailResponse:
        """
        Retrieve investor dashboard information.
        """

        profile = await self.profile_repository.get_active_by_id(user_id)

        if profile is None:
            raise ResourceNotFoundError("Investor not found")

        cash_account = await self.account_repository.get_user_cash_account(user_id)

        cash_balance        = Decimal("0")
        lifetime_deposits   = Decimal("0")
        recent_transactions = []

        if cash_account is not None:
            cash_balance      = await self.ledger_repository.get_account_balance(cash_account.id)
            lifetime_deposits = await self.ledger_repository.get_total_deposits(cash_account.id)

            recent_ledger_transactions = await self.ledger_repository.get_recent_transactions(cash_account.id, limit=10)
            recent_transactions = [
                InvestorTransactionResponse(
                    transaction_id=transaction.id,
                    transaction_type=transaction.reference_type.value,
                    amount=transaction.amount,
                    created_at=transaction.created_at,
                )
                for transaction in recent_ledger_transactions
            ]
        invested_amount = (
            await self.allocation_repository.get_total_invested_amount(
                user_id
            )
        )

        holding_count = (
            await self.allocation_repository.get_active_position_count(
                user_id
            )
        )

        allocations = (
            await self.allocation_repository.get_open_by_user_id(
                user_id
            )
        )

        positions = (
            await self.position_repository.get_by_ids(
                [
                    allocation.position_id
                    for allocation in allocations
                ]
            )
        )

        holdings = []
        for allocation in allocations:

            position = positions.get(
                allocation.position_id
            )

            if position is None:
                continue

            average_price = (
                    allocation.remaining_cost
                    / allocation.remaining_quantity
            ) if allocation.remaining_quantity > 0 else Decimal("0")

            holdings.append(
                InvestorHoldingResponse(
                    symbol=position.symbol,
                    quantity=allocation.remaining_quantity,
                    average_price=average_price,
                    invested_amount=allocation.remaining_cost,
                    current_price=None,
                )
            )

        return InvestorDetailResponse(
            profile=InvestorProfileResponse(
                id=profile.id,
                full_name=profile.full_name,
                is_active=profile.is_active,
                created_at=profile.created_at,
            ),
            summary=InvestorSummaryResponse(
                cash_balance=cash_balance,
                invested_amount=invested_amount,
                holding_count=holding_count,
                lifetime_deposits=lifetime_deposits,
            ),
            holdings=holdings,
            recent_transactions=recent_transactions,
        )

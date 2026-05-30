"""
Administrative investor API schemas.
"""

from datetime import datetime
from decimal  import Decimal
from uuid     import UUID

from fastapi import Query
from pydantic     import BaseModel, Field
from app.db.enums import UserRole

class AdminInvestorSummaryResponse(BaseModel):
    """
    Administrative investor summary payload.
    """
    deployable_cash_balance: Decimal
    full_name              : str
    role                   : UserRole
    is_active              : bool
    created_at             : datetime
    id                     : UUID
    active_position_count  : int

class PaginatedInvestorResponse(BaseModel):
    """
    Paginated investor listing response.
    """
    page_size  : int
    total      : int
    items      : list[AdminInvestorSummaryResponse]
    page       : int
    total_pages: int

class InvestorListQueryParams(BaseModel):
    """
    Investor list query parameters
    """
    page     : int        = Field(default=1, ge=1)
    page_size: int        = Field(default=20, ge=1, le=100)
    search   : str | None = Query(default=None)

class InvestorProfileResponse(BaseModel):
    id        : UUID
    full_name : str
    is_active : bool
    created_at: datetime

class InvestorSummaryResponse(BaseModel):
    cash_balance     : Decimal
    invested_amount  : Decimal
    holding_count    : int
    lifetime_deposits: Decimal

class InvestorHoldingResponse(BaseModel):
    symbol  : str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal | None

class InvestorTransactionResponse(BaseModel):
    transaction_type: str
    amount          : Decimal
    created_at      : datetime

class InvestorDetailResponse(BaseModel):
    profile: InvestorProfileResponse

    summary: InvestorSummaryResponse

    holdings: list[InvestorHoldingResponse]

    recent_transactions: list[InvestorTransactionResponse]
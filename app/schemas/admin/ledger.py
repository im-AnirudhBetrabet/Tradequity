"""
Administrative ledger API schemas
"""

from decimal import Decimal
from uuid    import UUID

from pydantic import BaseModel, Field

class AdminDepositRequest(BaseModel):
    """
    Administrative deposit request payload
    """

    user_id          : UUID
    amount           : Decimal = Field(gt=0)
    payment_method   : str = Field(min_length=1, max_length=50)
    payment_reference: str = Field(min_length=1, max_length=255)

class AdminDepositResponse(BaseModel):
    """
    Administrative deposit response payload
    """

    updated_cash_balance: Decimal
    amount              : Decimal
    user_id             : UUID
    transaction_id      : UUID

"""
Administrative trade request and response schemas.

This module defines API contracts for administrative trade executions,
operations, including pooled buy and sell workflows.

Design principles:
    - String request validation.
    - Explicit typed API contracts.
    - Business-safe numeric handling.
"""

from datetime import datetime
from decimal  import Decimal
from uuid     import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.enums import AssetType, TradeType

class AllocationInput(BaseModel):
    """
    Capital allocation input for pooled buy execution.

    Attributes:
        user_id:
            User receiving beneficial ownership.

        amount:
            Capital amount contributed by the user.
    """

    user_id: UUID
    amount : Decimal = Field(gt=0)

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, value: Decimal) -> Decimal:
        """
        Validate allocation amount precision
        Args:
            value:
                Submitted allocation amount.

        Returns:
            Decimal:
                Validated amount.

        Raises:
            ValueError:
                If amount precision exceeds supported limits.
        """
        if value.as_tuple().exponent < -8:
            raise ValueError("Allocation amount exceeds supported decimal precision")

        return value


class BuyTradeRequest(BaseModel):
    """
    Administrative pooled buy execution request.

    Attributes:
        symbol:
            Exchange trading symbol.

        instrument_name:
            Human-readable instrument name.

        asset_type:
            Investment asset classification.

        quantity:
            Executed trade quantity.

        price:
            Per-unit execution price.

        charges:
            Execution charges.

        executed_at:
            Trade execution timestamp.

        notes:
            Optional administrative notes.

        allocations:
            User capital allocation instructions.
    """

    symbol         : str = Field(min_length=1, max_length=50)
    instrument_name: str = Field(min_length=1, max_length=255)
    asset_type     : AssetType

    quantity: Decimal = Field(gt=0)
    price   : Decimal = Field(gt=0)
    charges : Decimal = Field(ge=0)

    executed_at: datetime
    notes      : str | None = Field(default=None, max_length=2000)

    allocations: list[AllocationInput] = Field(min_length=1)

    @field_validator("quantity", "price", "charges")
    @classmethod
    def validate_decimal_precision(cls,value: Decimal) -> Decimal:
        """
        Validate monetary and quantity precision.

        Args:
            value:
                Submitted decimal value.

        Returns:
            Decimal:
                Validated decimal.

        Raises:
            ValueError:
                If precision exceeds supported limits.
        """
        if value.as_tuple().exponent < -8:
            raise ValueError("Decimal precision exceeds supported limits")

        return value


class SellTradeRequest(BaseModel):
    """
    Administrative sell execution request.

    Attributes:
        position_id:
            Target master position.

        quantity:
            Quantity to liquidate.

        price:
            Per-unit execution price.

        charges:
            Execution charges.

        executed_at:
            Sell execution timestamp.

        notes:
            Optional administrative notes.
    """

    position_id: UUID
    quantity   : Decimal = Field(gt=0)
    price      : Decimal = Field(gt=0)
    charges    : Decimal = Field(ge=0)
    executed_at: datetime
    notes      : str | None = Field(default=None, max_length=2000)

    @field_validator("quantity", "price", "charges")
    @classmethod
    def validate_decimal_precision(cls,value: Decimal) -> Decimal:
        """
        Validate decimal precision.

        Args:
            value:
                Submitted decimal value.

        Returns:
            Decimal:
                Validated decimal.
        """
        if value.as_tuple().exponent < -8:
            raise ValueError(
                "Decimal precision exceeds supported limits"
            )

        return value


class TradeExecutionResponse(BaseModel):
    """
    Trade execution response payload.
    """

    model_config = ConfigDict(from_attributes=True)

    id             : UUID
    trade_type     : TradeType
    symbol         : str
    instrument_name: str
    asset_type     : AssetType
    quantity       : Decimal
    price          : Decimal
    charges        : Decimal
    executed_at    : datetime
    created_at     : datetime


class BuyTradeResponse(BaseModel):
    """
    Administrative buy workflow response payload.
    """

    trade                 : TradeExecutionResponse
    position_id           : UUID
    total_allocated_amount: Decimal
    allocation_count      : int


class SellTradeResponse(BaseModel):
    """
    Administrative sell workflow response payload.
    """

    trade               : TradeExecutionResponse
    realized_allocations: int
    total_net_credit    : Decimal
    total_fee_collected : Decimal
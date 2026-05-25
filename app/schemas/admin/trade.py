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
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.enums import AssetType, TradeType, SellMode

class AllocationInput(BaseModel):
    """
    Share allocation input for pooled buy execution.

    Attributes:
        user_id:
            User receiving beneficial ownership.

        quantity:
            Whole shares assigned to the user.
    """

    user_id : UUID
    quantity: Decimal = Field(gt=Decimal("0"), description="Whole shares allocated to user")

    @field_validator("quantity")
    @classmethod
    def validate_whole_quantity(cls, value: Decimal) -> Decimal:
        """
        Validate if the quantity is a whole number.
        Args:
            value:
                Submitted allocation quantity.

        Returns:
            Decimal:
                Validated quantity.

        Raises:
            ValueError:
                If allocation quantity is not a whole number.
        """
        if value != value.to_integral_value():
            raise ValueError("Quantity must be a whole number")
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

    @model_validator(mode="after")
    def validate_allocations(self):
        """
        Ensure allocated quantities match executed quantity.
        """

        total_allocated = sum(allocation.quantity for allocation in self.allocations)

        if total_allocated != self.quantity:
            raise ValueError(
                "Allocated quantity must equal trade quantity"
            )

        return self

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

        mode:
            Sell execution strategy.

        target_user_id:
            Required only for targeted liquidation.
    """

    position_id   : UUID
    quantity      : Decimal     = Field(gt=0)
    price         : Decimal     = Field(gt=0)
    charges       : Decimal     = Field(ge=0)
    executed_at   : datetime
    notes         : str | None  = Field(default=None, max_length=2000)
    mode          : SellMode    = SellMode.PROPORTIONAL
    target_user_id: UUID | None = None

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

    @field_validator("target_user_id")
    @classmethod
    def validate_targeted_mode(cls, value: UUID | None, info) -> UUID | None:
        """
        Validate targeted sell requirements.
        """
        mode = info.data.get("mode")

        if mode == SellMode.TARGETED and value is None:
            raise ValueError("target_user_id is required for targeted sell.")

        if mode == SellMode.PROPORTIONAL and value is not None:
            raise ValueError("target_user_id should not be provided for proportional sell")

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

    trade                   : TradeExecutionResponse
    position_id             : UUID
    total_allocated_quantity: Decimal
    allocation_count        : int


class SellTradeResponse(BaseModel):
    """
    Administrative sell workflow response payload.
    """

    trade               : TradeExecutionResponse
    realized_allocations: int
    total_net_credit    : Decimal
    total_fee_collected : Decimal
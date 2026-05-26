from pydantic import BaseModel, Field, model_validator, field_validator
from decimal  import Decimal
from uuid     import UUID

from app.db.enums import SuggestionStrategy


class AllocationSuggestionRequest(BaseModel):
    """
    Request payload for allocation suggestions.
    """
    symbol: str     = Field(min_length=1, max_length=50)
    price : Decimal = Field(gt=Decimal("0"))

    estimated_charges: Decimal = Field(ge=Decimal("0"))
    target_quantity  : Decimal = Field(gt=Decimal("0"))

    candidate_user_ids: list[UUID] = Field(min_length=1)

    @field_validator("price", "estimated_charges", "target_quantity")
    @classmethod
    def validate_precision(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.00000001"))

    @field_validator("target_quantity")
    @classmethod
    def validate_whole_quantity(cls, value:Decimal) -> Decimal:
        if value != value.to_integral_value():
            raise ValueError(f"Target quantity must be a whole number. Expected {value.to_integral_value()} buy got {value}")
        return value

    @model_validator(mode="after")
    def validate_unique_candidates(self):
        if len(self.candidate_user_ids) != len(set(self.candidate_user_ids)):
            raise ValueError("Duplicate candidate users are not allowed")

        return self

class SuggestedAllocation(BaseModel):
    """
    Suggested allocation for a single user.
    """

    user_id       : UUID
    quantity      : Decimal
    estimated_cost: Decimal
    available_cash: Decimal

class AllocationSuggestionOption(BaseModel):
    """
    Strategy output option.
    """
    strategy           : SuggestionStrategy
    achievable_quantity: Decimal
    allocations        : list[SuggestedAllocation]

class AllocationSuggestionResponse(BaseModel):
    """
    Allocation suggestion response payload.
    """

    requested_quantity: Decimal
    price             : Decimal
    symbol            : str
    options           : list[AllocationSuggestionOption]

"""User profile schema placeholder."""

from datetime import datetime
from decimal  import Decimal
from uuid     import UUID
from pydantic import BaseModel

from app.db.enums import UserRole

class CurrentUserResponse(BaseModel):
    """
    Authenticated user profile response:

    Attributes:
        id:
            Application user identifier

        full_name:
            Registered display name.

        role:
            Authorization role

        is_active:
            Whether the profile is active.

        minimum_profit_threshold:
            User-specific minimum profit threshold.

        created_at:
            Profile creation timestamp.

        updated_at:
            Last profile update timestamp.

    """
    id                      : UUID
    full_name               : str
    role                    : UserRole
    is_active               : bool
    minimum_profit_threshold: Decimal | None
    created_at              : datetime
    updated_at              : datetime
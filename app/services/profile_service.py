"""
Profile business services.

This module contains application workflows related to
user profile operations.
"""

from uuid import UUID

from app.core.exceptions                 import ResourceNotFoundError
from app.repositories.profile_repository import ProfileRepository
from app.schemas.user.profile            import CurrentUserResponse
from sqlalchemy.ext.asyncio              import AsyncSession

class ProfileService:
    """
    Profile application service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.profile_repository = ProfileRepository(db)


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

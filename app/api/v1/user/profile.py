"""
User Profile APIs

This module exposes authenticated user profile operations
"""

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps.auth      import AuthenticatedUser, get_current_user
from app.db.session         import get_db_session

from app.schemas.user.profile     import UpdateProfileRequest, CurrentUserResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.patch("/me", response_model=CurrentUserResponse)
async def update_current_profile(request: UpdateProfileRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)) -> CurrentUserResponse:
    """
    Update authenticated user profile.
    """

    profile_service = ProfileService(db)

    return await profile_service.update_current_user_profile(user_id=current_user.user_id, request=request)



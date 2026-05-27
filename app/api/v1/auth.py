"""
Authentication API routes.

This module exposes authentication-related endpoints
for authenticated user workflows.
"""

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps.auth      import AuthenticatedUser, get_current_user
from app.db.session         import get_db_session

from app.schemas.user.profile            import CurrentUserResponse
from app.services.profile_service        import ProfileService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/me", response_model=CurrentUserResponse)
async def get_current_authenticated_user(current_user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)) -> CurrentUserResponse:
    """
    Return authenticated application user profile.
    """
    profile_service = ProfileService(db)

    return await profile_service.get_current_user_profile(user_id=current_user.user_id)


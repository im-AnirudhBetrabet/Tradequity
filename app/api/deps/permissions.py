"""
Authorization dependencies for FastAPI routes.

This module provides reusable authorization checks for protected routes,
including administrative access enforcement.

Design principles:
    - Separation of authentication and authorization.
    - Reusable FastAPI dependency injection.
    - Database-backed role validation.
    - Explicit authorization failure semantics.
"""

from fastapi                             import Depends, HTTPException
from sqlalchemy.ext.asyncio              import AsyncSession
from app.api.deps.auth                   import AuthenticatedUser, get_current_user
from app.db.enums                        import UserRole
from app.db.session                      import get_db_session
from app.repositories.profile_repository import ProfileRepository


async def require_admin(
        current_user: AuthenticatedUser = Depends(get_current_user),
        db          : AsyncSession      = Depends(get_db_session)
) -> AuthenticatedUser:
    """
    Enforce administrative access for protected routes.

    This dependency validates that the authenticated user exists in the application
    profile store and possess administrative privileges

    Args:
        current_user:
            Authenticated user context extracted from JWT validation.

        db:
            Active asynchronous database session.

    Returns:
        AuthenticatedUser:
            The authenticated admin user context.

    Raises:
         HTTPException:
            403 if the user lacks administrative privileges.
            404 if the profile record cannot be found.
    """
    profile_repo = ProfileRepository(db)
    profile      = await profile_repo.get_active_by_id(current_user.user_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    if profile.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Administrative access required"
        )

    return current_user
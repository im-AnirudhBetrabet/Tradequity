"""
Profile repository implementations.

This module provides persistence access methods for application user
profile records.

Design principles:
    - Persistence-only responsibilities
    - Async SQLAlchemy access patterns
    - Transaction-safe profile mutation support
"""

from uuid                   import UUID
from sqlalchemy             import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.enums           import UserRole
from app.db.models.profile  import Profile
from app.db.models.account  import Account
from app.db.enums           import AccountType, UserRole


class ProfileRepository:
    """
    Repository for application profile persistence operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the repository.

        Args:
            db:
                Active asynchronous database session.
        """
        self.db = db

    async def create(self,profile: Profile) -> Profile:
        """
        Persist a new profile record.

        Args:
            profile:
                Profile entity to persist.

        Returns:
            Profile:
                Persisted profile entity.
        """
        self.db.add(profile)
        await self.db.flush()

        return profile

    async def get_by_id(self,user_id: UUID) -> Profile | None:
        """
        Retrieve a profile by identifier.

        Args:
            user_id:
                Target user profile identifier.

        Returns:
            Profile | None:
                Matching profile if found.
        """
        stmt = select(Profile).where(Profile.id == user_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id_for_update( self, user_id: UUID ) -> Profile | None:
        """
        Retrieve and lock a profile for transactional mutation.

        Args:
            user_id:
                Target user profile identifier.

        Returns:
            Profile | None:
                Locked profile if found.
        """
        stmt = (
            select(Profile)
            .where(Profile.id == user_id)
            .with_for_update()
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_active_by_id(self,user_id: UUID) -> Profile | None:
        """
        Retrieve an active profile by identifier.

        Args:
            user_id:
                Target user profile identifier.

        Returns:
            Profile | None:
                Matching active profile if found.
        """
        stmt = select(Profile).where(
            Profile.id == user_id,
            Profile.is_active.is_(True),
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_admin_profiles(self) -> list[Profile]:
        """
        Retrieve all active administrative profiles.

        Returns:
            list[Profile]:
                Active admin profiles.
        """
        stmt = select(Profile).where(
            Profile.is_admin.is_(True),
            Profile.is_active.is_(True),
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def update(self,profile: Profile) -> Profile:
        """
        Flush updates for a mutated profile entity.

        Args:
            profile:
                Mutated profile entity.

        Returns:
            Profile:
                Updated profile entity.
        """
        await self.db.flush()

        return profile

    async def update_full_name(self, user_id: UUID, full_name: str) -> Profile | None:
        """
        Update profile display name.

        Args:
            user_id:
                Target profile identifier.

            full_name:
                Updated display name.

        Returns:
            Profile | None:
                Updated profile entity if found or None
        """

        profile = await self.get_by_id(user_id)

        if profile is None:
            return None

        profile.full_name = full_name

        await self.db.flush()

        await self.db.refresh(profile)

        return profile

    async def search_investors(self, page: int, page_size: int, search: str | None) -> tuple[list[Profile], int]:
        """
        Retrieve paginated investor profiles.

        Args:
            page:
                Requested page number.

            page_size:
                Requested page size.

            search:
                Optional investor name search.

        Returns:
            tuple[list[Profile], int]:
                Matching profiles and total count.
        """

        stmt = select(Profile).where(
            Profile.role == UserRole.INVESTOR
        )

        if search:
            stmt = stmt.where(
                Profile.full_name.ilike(f"%{search}%")
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())

        total_result = await self.db.execute(count_stmt)

        total = total_result.scalar_one()

        stmt = stmt.order_by(Profile.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)

        profiles = list(result.scalars().all())

        return profiles, total
"""Admin users endpoints (placeholder)."""
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio       import AsyncSession
from app.schemas.admin.user import PaginatedInvestorResponse, InvestorDetailResponse
from app.services.profile_service import ProfileService
from app.db.session               import get_db_session
from app.api.deps.permissions     import require_admin
from uuid                         import UUID

router = APIRouter(
    prefix="/admin/investors",
    tags=["Admin investor Search"]
)

@router.get("", response_model=PaginatedInvestorResponse)
async def list_investors(page: int = Query(default=1, ge=1), page_size: int = Query(default=12, ge=1, le=100), search: str | None = Query(default=None), db: AsyncSession = Depends(get_db_session), current_user = Depends(require_admin)):
    """
    Retrieve paginated investor summaries.
    """
    service = ProfileService(db=db)

    return await service.list_investors(page=page, page_size=page_size, search=search)

@router.get("/{user_id}", response_model=InvestorDetailResponse)
async def get_investor_detail(user_id: UUID, db: AsyncSession = Depends(get_db_session), current_user = Depends(require_admin)):
    """
    Retrieve investor detail dashboard.
    """
    service = ProfileService(db=db)

    return await service.get_investor_details(user_id)

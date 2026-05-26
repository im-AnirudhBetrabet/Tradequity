"""
Administrative allocation advisory APIs.

This module exposes allocation intelligence endpoints used
by administrators to generate allocation suggestions before
execution trades.
"""

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio   import AsyncSession
from app.api.deps.permissions import require_admin
from app.db.session           import get_db_session

from app.schemas.admin.allocation               import AllocationSuggestionRequest, AllocationSuggestionResponse
from app.services.allocation_suggestion_service import AllocationSuggestionService

router = APIRouter(prefix="/allocations", tags=["Admin Allocations"])

@router.post("/suggestions", response_model=AllocationSuggestionResponse)
async def get_allocation_suggestions(request: AllocationSuggestionRequest, db: AsyncSession= Depends(get_db_session), current_user = Depends(require_admin)) -> AllocationSuggestionResponse:
    """
    Generate advisory allocation suggestions.

    This endpoint does not execute any trades.

    It produces whole-share allocation suggestion for
    selected users based on:
        - available deployable cash.
        - target trade quantity.
        - estimated execution charges.
        - allocation strategy heuristics.

    Args:
        request:
            Allocation suggestion request
        db:
            Asynchronous Database session.
        current_user:
            Administrative actor.

    Returns:
        AllocationSuggestionResponse
    """

    service = AllocationSuggestionService(db)

    return await service.generate_suggestions(request)
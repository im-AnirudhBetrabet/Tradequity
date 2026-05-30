"""
Administrative ledger APIs
"""

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.permissions    import require_admin
from app.db.session              import get_db_session
from app.schemas.admin.ledger    import AdminDepositResponse, AdminDepositRequest
from app.services.ledger_service import LedgerService

router=APIRouter(
    prefix="/admin/ledger",
    tags=["Admin Ledger"]
)

@router.post("/deposit", response_model=AdminDepositResponse)
async def record_deposit(request: AdminDepositRequest, db: AsyncSession = Depends(get_db_session), current_user = Depends(require_admin)) -> AdminDepositResponse:
    """
    Record investor deposit
    """
    service = LedgerService(db)

    return await service.record_deposit(request)
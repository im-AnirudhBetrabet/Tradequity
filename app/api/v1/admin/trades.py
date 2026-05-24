"""
Administrative trade execution API routes.

This module exposes protected administrative trade execution endpoints
for pooled investment workflows.
"""

from fastapi                import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.permissions  import require_admin
from app.api.deps.auth         import AuthenticatedUser
from app.db.session            import get_db_session
from app.services.buy_service  import BuyService
from app.services.sell_service import SellService
from app.schemas.admin.trade   import BuyTradeRequest, BuyTradeResponse, SellTradeResponse, SellTradeRequest

router = APIRouter(prefix="/admin/trades", tags=["Admin Trades"])

@router.post("/buy", response_model=BuyTradeResponse, summary="Execute pooled buy trade")
async def execute_buy_trade(request: BuyTradeRequest, current_user: AuthenticatedUser = Depends(require_admin), db: AsyncSession = Depends(get_db_session)) -> BuyTradeResponse:
    """
    Execute a pooled administrative buy trade.

    This endpoint records a platform buy execution, creates the pooled
    master position, derives beneficial ownership allocations, and moves
    user capital into platform treasury.

    Args:
        request:
            Administrative buy request payload.

        current_user:
            Authenticated administrative user context.

        db:
            Active asynchronous database session.

    Returns:
        BuyTradeResponse:
            Buy workflow execution summary.
    """
    service = BuyService(db)

    return await service.execute_buy(request=request, admin_user_id=current_user.user_id)

@router.post("/sell", response_model=SellTradeResponse, summary="Execute pooled sell trade")
async def execute_sell_trade(request: SellTradeRequest, current_user: AuthenticatedUser = Depends(require_admin), db: AsyncSession = Depends(get_db_session)) -> SellTradeResponse:
    """
    Execute pooled sell workflow.

    Supports:
        - proportional pooled liquidation
        - targeted investor liquidation

    Args:
        request:
            Sell execution payload.

        current_user:
            Authenticated administrative actor.

        db:
            Active database session.

    Returns:
        SellTradeResponse:
            Sell execution summary.
    """
    service = SellService(db)

    return await service.execute_sell(
        request=request,
        admin_user_id=current_user.user_id,
    )
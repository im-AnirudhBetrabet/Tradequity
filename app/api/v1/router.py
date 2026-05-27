from fastapi import APIRouter

from app.api.v1.admin.trades      import router as admin_trades_router
from app.api.v1.admin.allocations import router as allocation_suggestion_router
from app.api.v1.auth              import router as auth_router
from app.api.v1.user.profile      import router as profile_router
api_router = APIRouter()

api_router.include_router(admin_trades_router)
api_router.include_router(allocation_suggestion_router)
api_router.include_router(auth_router)
api_router.include_router(profile_router)
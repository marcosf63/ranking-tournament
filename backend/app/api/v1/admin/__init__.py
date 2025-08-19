from fastapi import APIRouter
from .players import router as players_router
from .scores import router as scores_router
from .tournaments import router as tournaments_router
from .admins import router as admins_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(players_router)
admin_router.include_router(scores_router)
admin_router.include_router(tournaments_router)
admin_router.include_router(admins_router)
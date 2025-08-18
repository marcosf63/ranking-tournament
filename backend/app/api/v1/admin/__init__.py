from fastapi import APIRouter
from .players import router as players_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(players_router)
from fastapi import APIRouter
from .ranking import router as ranking_router
from .search import router as search_router

public_router = APIRouter(prefix="/public")
public_router.include_router(ranking_router)
public_router.include_router(search_router)
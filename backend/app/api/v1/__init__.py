from fastapi import APIRouter
from .auth import router as auth_router
from .admin import admin_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_router)
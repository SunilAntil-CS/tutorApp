from fastapi import APIRouter

from api.v1 import content

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(content.router, prefix="/content", tags=["content"])

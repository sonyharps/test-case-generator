from fastapi import APIRouter
from app.api.v1.routes_tc import router as tc_router
from app.api.v1.routes_negative import router as negative_router
from app.api.v1.routes_export import router as export_router

api_router = APIRouter()

api_router.include_router(tc_router, prefix="/tc", tags=["Test Case Generator"])
api_router.include_router(negative_router, prefix="/negative", tags=["Negative TC"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])
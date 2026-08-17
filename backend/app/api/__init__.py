from fastapi import APIRouter

from app.api import admin, auth, directory, inspections, ops, sync, work_orders

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(directory.router)
api_router.include_router(inspections.router)
api_router.include_router(work_orders.router)
api_router.include_router(ops.router)
api_router.include_router(sync.router)
api_router.include_router(admin.router)

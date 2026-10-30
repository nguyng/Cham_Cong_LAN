from fastapi import APIRouter

system_router = APIRouter(tags=["System"])
auth_router = APIRouter(tags=["Authentication"])
organization_router = APIRouter(tags=["Organization"])
attendance_router = APIRouter(tags=["Attendance"])
leave_router = APIRouter(tags=["Leave"])
security_router = APIRouter(tags=["Security"])
admin_router = APIRouter(tags=["Administration"])

ALL_ROUTERS = (
    system_router,
    auth_router,
    organization_router,
    attendance_router,
    leave_router,
    security_router,
    admin_router,
)

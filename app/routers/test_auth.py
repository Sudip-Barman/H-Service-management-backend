from fastapi import APIRouter, Depends

from app.models.user import User
from app.core.dependencies import (
    get_current_user,
    require_admin,
    require_role,
)


router = APIRouter(
    prefix="/api/test",
    tags=["Authorization Test"]
)


@router.get("/protected")
def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "You are authenticated",
        "user": current_user.name,
        "role": current_user.role
    }


@router.get("/admin")
def admin_route(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "Admin access granted",
        "user": current_user.name,
        "role": current_user.role
    }


@router.get("/admin-receptionist")
def admin_receptionist_route(
    current_user: User = Depends(
        require_role("admin", "receptionist")
    )
):
    return {
        "message": "Admin or receptionist access granted",
        "user": current_user.name,
        "role": current_user.role
    }
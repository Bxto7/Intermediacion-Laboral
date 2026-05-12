# RF: RF136-RF145 (M09) — Panel admin DRTPE-Junín. Todos los endpoints requieren ADMIN.
from fastapi import APIRouter, Depends

from app.core.security import UserRole, require_role

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)

# Side-effect import: registers dashboard routes onto admin_router
from app.api.v1.admin import dashboard as _dashboard  # noqa: E402, F401

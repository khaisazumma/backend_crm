import asyncpg
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.dependencies import require_role
from app.schemas.admin import AdminCreate, LoginRequest, LoginResponse
from app.services.auth_service import authenticate_admin, create_admin

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, pool: asyncpg.Pool = Depends(get_db)):
    result = await authenticate_admin(pool, payload.email, payload.password)
    return result


@router.post("/admins", dependencies=[Depends(require_role("SUPER_ADMIN"))])
async def create_new_admin(payload: AdminCreate, pool: asyncpg.Pool = Depends(get_db)):
    """Hanya SUPER_ADMIN yang boleh membuat akun admin baru."""
    return await create_admin(pool, payload.email, payload.password, payload.role.value)

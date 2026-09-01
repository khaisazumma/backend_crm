import asyncpg
from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.services import commission_service

router = APIRouter(
    prefix="/commissions",
    tags=["Commissions"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("")
async def list_commissions(
    sales_id: int | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db),
):
    return await commission_service.list_commissions(pool, sales_id, limit, offset)

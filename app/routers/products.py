import asyncpg
from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import get_current_admin, require_role
from app.schemas.product import ProductCreate, ProductListOut, ProductOut, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductListOut])
async def list_products(
    product_type: str | None = None,
    is_active: bool | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db),
):
    """Publik (dipakai juga oleh katalog di frontend) — tidak wajib login."""
    return await product_service.list_products(pool, product_type, is_active, limit, offset)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, pool: asyncpg.Pool = Depends(get_db)):
    return await product_service.get_product(pool, product_id)


@router.post(
    "",
    response_model=ProductOut,
    status_code=201,
    dependencies=[Depends(require_role("SUPER_ADMIN", "ADMIN"))],
)
async def create_product(payload: ProductCreate, pool: asyncpg.Pool = Depends(get_db)):
    return await product_service.create_product(pool, payload)


@router.put(
    "/{product_id}",
    response_model=ProductOut,
    dependencies=[Depends(require_role("SUPER_ADMIN", "ADMIN"))],
)
async def update_product(product_id: int, payload: ProductUpdate, pool: asyncpg.Pool = Depends(get_db)):
    return await product_service.update_product(pool, product_id, payload)


@router.patch(
    "/{product_id}/deactivate",
    status_code=204,
    dependencies=[Depends(require_role("SUPER_ADMIN", "ADMIN"))],
)
async def deactivate_product(product_id: int, pool: asyncpg.Pool = Depends(get_db)):
    await product_service.deactivate_product(pool, product_id)


@router.delete(
    "/{product_id}",
    status_code=204,
    dependencies=[Depends(require_role("SUPER_ADMIN"))],
)
async def delete_product(product_id: int, pool: asyncpg.Pool = Depends(get_db)):
    """
    Hapus permanen — hanya berhasil kalau produk belum pernah dipakai
    di invoice manapun (dijaga oleh FK RESTRICT). Kalau sudah pernah
    dipakai, gunakan endpoint /deactivate saja.
    """
    await product_service.delete_product_hard(pool, product_id)

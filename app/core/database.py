"""
Connection pool asyncpg — dipakai semua service lewat dependency `get_db`.
Tidak pakai ORM: semua query ditulis sebagai SQL mentah di app/services/*.
"""
import asyncpg
from fastapi import Request

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_dsn,
        min_size=settings.DB_POOL_MIN_SIZE,
        max_size=settings.DB_POOL_MAX_SIZE,
        ssl="require" if settings.DB_SSL else None,
    )


async def disconnect_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool belum diinisialisasi. Pastikan connect_db() sudah dipanggil.")
    return _pool


async def get_db(request: Request = None) -> asyncpg.Pool:
    """
    Dependency FastAPI: `pool = Depends(get_db)`.
    Setiap service memanggil `async with pool.acquire() as conn:` sendiri
    supaya bisa dibungkus transaksi (conn.transaction()) saat perlu
    (contohnya create_invoice yang harus atomik).
    """
    return get_pool()
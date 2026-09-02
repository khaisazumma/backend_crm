import asyncpg
from fastapi import HTTPException, status

from app.schemas.customer import CustomerCreate, CustomerUpdate


async def list_customers(pool: asyncpg.Pool, search: str | None, limit: int, offset: int) -> list[dict]:
    async with pool.acquire() as conn:
        if search:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    id_client,
                    nama,
                    email,
                    telepon,
                    provinsi,
                    kabupaten_kota,
                    komoditas,
                    luas_tambak
                FROM customers
                WHERE nama ILIKE '%' || $1 || '%'
                   OR telepon ILIKE '%' || $1 || '%'
                ORDER BY id DESC
                LIMIT $2 OFFSET $3
                """,
                search,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    id_client,
                    nama,
                    email,
                    telepon,
                    provinsi,
                    kabupaten_kota,
                    komoditas,
                    luas_tambak
                FROM customers
                ORDER BY id DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

    return [dict(r) for r in rows]

async def get_customer(pool: asyncpg.Pool, customer_id: int) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM customers WHERE id = $1", customer_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer tidak ditemukan")
    return dict(row)


async def create_customer(pool: asyncpg.Pool, data: CustomerCreate) -> dict:
    async with pool.acquire() as conn:
        # id_client = MAX(id_client) + 1, sesuai perilaku backend lama
        next_id_client = await conn.fetchval("SELECT COALESCE(MAX(id_client), 0) + 1 FROM customers")
        row = await conn.fetchrow(
            """
            SELECT * FROM fn_customer_create(
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            ) AS id
            """,
            next_id_client,
            data.nama,
            data.gender,
            data.email,
            data.telepon,
            data.alamat_domisili,
            data.alamat_usaha,
            data.provinsi,
            data.kabupaten_kota,
            data.kecamatan,
            data.kelurahan_desa,
            data.jenis_peternak,
            data.komoditas,
            data.luas_tambak,
            data.teknologi,
            data.padat_tebar,
        )
    return await get_customer(pool, row["id"])


async def update_customer(pool: asyncpg.Pool, customer_id: int, data: CustomerUpdate) -> dict:
    async with pool.acquire() as conn:
        found = await conn.fetchval(
            """
            SELECT fn_customer_update($1, $2, $3, $4, $5, $6, $7)
            """,
            customer_id,
            data.nama,
            data.gender,
            data.email,
            data.telepon,
            data.alamat_domisili,
            data.alamat_usaha,
        )
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer tidak ditemukan")
    return await get_customer(pool, customer_id)


async def delete_customer(pool: asyncpg.Pool, customer_id: int) -> None:
    async with pool.acquire() as conn:
        found = await conn.fetchval("SELECT fn_customer_delete($1)", customer_id)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer tidak ditemukan")

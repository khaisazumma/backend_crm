import asyncpg
from fastapi import HTTPException, status

from app.schemas.product import ProductCreate, ProductUpdate


def _row_to_product_out(row: asyncpg.Record) -> dict:
    d = dict(row)
    feederve_attrs = None
    kincirve_attrs = None
    if d.get("feederve_version") is not None:
        feederve_attrs = {
            "version": d["feederve_version"],
            "motor_type": d["feederve_motor_type"],
            "thrower": d["feederve_thrower"],
            "measurer": d["feederve_measurer"],
        }
    if d.get("kincirve_version") is not None:
        kincirve_attrs = {
            "version": d["kincirve_version"],
            "phase": d["kincirve_phase"],
            "gearbox": d["kincirve_gearbox"],
            "material": d["kincirve_material"],
            "spline": d["kincirve_spline"],
            "fan": d["kincirve_fan"],
        }
    return {
        "id": d["id"],
        "product_type": d["product_type"],
        "sku": d["sku"],
        "type": d["type"],
        "category": d["category"],
        "description": d["description"],
        "specification": d["specification"],
        "normal_price": d["normal_price"],
        "discount_price": d["discount_price"],
        "stock": d["stock"],
        "is_active": d["is_active"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
        "feederve_attributes": feederve_attrs,
        "kincirve_attributes": kincirve_attrs,
    }


async def list_products(
    pool: asyncpg.Pool,
    product_type: str | None,
    is_active: bool | None,
    limit: int,
    offset: int,
) -> list[dict]:
    query = """
        SELECT
            type AS product,
            category,
            COALESCE(discount_price, normal_price) AS price,
            stock
        FROM v_products_full
        WHERE 1=1
    """

    params: list = []

    if product_type:
        params.append(product_type)
        query += f" AND product_type = ${len(params)}"

    if is_active is not None:
        params.append(is_active)
        query += f" AND is_active = ${len(params)}"

    params.extend([limit, offset])

    query += f"""
        ORDER BY id DESC
        LIMIT ${len(params) - 1}
        OFFSET ${len(params)}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(row) for row in rows]

async def get_product(pool: asyncpg.Pool, product_id: int) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM v_products_full WHERE id = $1", product_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")
    return _row_to_product_out(row)


async def create_product(pool: asyncpg.Pool, data: ProductCreate) -> dict:
    async with pool.acquire() as conn:
        async with conn.transaction():
            product_id = await conn.fetchval(
                "SELECT fn_product_create($1,$2,$3,$4,$5,$6,$7,$8,$9)",
                data.product_type.value,
                data.type,
                data.category,
                data.description,
                data.specification,
                data.normal_price,
                data.stock,
                data.sku,
                data.discount_price,
            )
            if data.product_type.value == "feederve" and data.feederve_attributes:
                fa = data.feederve_attributes
                await conn.execute(
                    """
                    INSERT INTO feederve_attributes (product_id, version, motor_type, thrower, measurer)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    product_id,
                    fa.version,
                    fa.motor_type,
                    fa.thrower,
                    fa.measurer,
                )
            if data.product_type.value == "kincirve" and data.kincirve_attributes:
                ka = data.kincirve_attributes
                await conn.execute(
                    """
                    INSERT INTO kincirve_attributes (product_id, version, phase, gearbox, material, spline, fan)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    product_id,
                    ka.version,
                    ka.phase,
                    ka.gearbox,
                    ka.material,
                    ka.spline,
                    ka.fan,
                )
    return await get_product(pool, product_id)


async def update_product(pool: asyncpg.Pool, product_id: int, data: ProductUpdate) -> dict:
    async with pool.acquire() as conn:
        async with conn.transaction():
            found = await conn.fetchval(
                """
                SELECT fn_product_update($1,$2,$3,$4,$5,$6,$7,$8,$9)
                """,
                product_id,
                data.type,
                data.category,
                data.description,
                data.specification,
                data.normal_price,
                data.discount_price,
                data.stock,
                data.is_active,
            )
            if not found:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

            if data.feederve_attributes:
                fa = data.feederve_attributes
                await conn.execute(
                    """
                    INSERT INTO feederve_attributes (product_id, version, motor_type, thrower, measurer)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (product_id) DO UPDATE SET
                        version = EXCLUDED.version,
                        motor_type = EXCLUDED.motor_type,
                        thrower = EXCLUDED.thrower,
                        measurer = EXCLUDED.measurer
                    """,
                    product_id,
                    fa.version,
                    fa.motor_type,
                    fa.thrower,
                    fa.measurer,
                )
            if data.kincirve_attributes:
                ka = data.kincirve_attributes
                await conn.execute(
                    """
                    INSERT INTO kincirve_attributes (product_id, version, phase, gearbox, material, spline, fan)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (product_id) DO UPDATE SET
                        version = EXCLUDED.version,
                        phase = EXCLUDED.phase,
                        gearbox = EXCLUDED.gearbox,
                        material = EXCLUDED.material,
                        spline = EXCLUDED.spline,
                        fan = EXCLUDED.fan
                    """,
                    product_id,
                    ka.version,
                    ka.phase,
                    ka.gearbox,
                    ka.material,
                    ka.spline,
                    ka.fan,
                )
    return await get_product(pool, product_id)


async def deactivate_product(pool: asyncpg.Pool, product_id: int) -> None:
    async with pool.acquire() as conn:
        found = await conn.fetchval("SELECT fn_product_deactivate($1)", product_id)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")


async def delete_product_hard(pool: asyncpg.Pool, product_id: int) -> None:
    async with pool.acquire() as conn:
        try:
            found = await conn.fetchval("SELECT fn_product_delete_hard($1)", product_id)
        except asyncpg.RaiseError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

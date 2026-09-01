import asyncpg


async def list_commissions(pool: asyncpg.Pool, sales_id: int | None, limit: int, offset: int) -> list[dict]:
    query = "SELECT * FROM commissions WHERE 1=1"
    params: list = []
    if sales_id:
        params.append(sales_id)
        query += f" AND sales_id = ${len(params)}"
    params.extend([limit, offset])
    query += f" ORDER BY id DESC LIMIT ${len(params) - 1} OFFSET ${len(params)}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]

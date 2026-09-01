import asyncpg
from fastapi import HTTPException, status

from app.schemas.cart import CartItemCreate, CartItemUpdate


async def _get_or_create_cart(conn: asyncpg.Connection, customer_id: int) -> asyncpg.Record:
    cart = await conn.fetchrow("SELECT * FROM marketplace_cart WHERE customer_id = $1", customer_id)
    if cart is None:
        cart = await conn.fetchrow(
            "INSERT INTO marketplace_cart (customer_id) VALUES ($1) RETURNING *",
            customer_id,
        )
    return cart


async def get_cart(pool: asyncpg.Pool, customer_id: int) -> dict:
    async with pool.acquire() as conn:
        cart = await _get_or_create_cart(conn, customer_id)
        items = await conn.fetch(
            "SELECT * FROM marketplace_cart_items WHERE cart_id = $1 ORDER BY id",
            cart["id"],
        )
    return {**dict(cart), "items": [dict(i) for i in items]}


async def add_item(pool: asyncpg.Pool, customer_id: int, data: CartItemCreate) -> dict:
    async with pool.acquire() as conn:
        async with conn.transaction():
            cart = await _get_or_create_cart(conn, customer_id)
            product = await conn.fetchrow(
                "SELECT normal_price, discount_price, is_active FROM products WHERE id = $1",
                data.product_id,
            )
            if product is None or not product["is_active"]:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan/nonaktif")

            await conn.execute(
                """
                INSERT INTO marketplace_cart_items
                    (cart_id, product_id, quantity, price_at_add, discount_price_at_add)
                VALUES ($1, $2, $3, $4, $5)
                """,
                cart["id"],
                data.product_id,
                data.quantity,
                product["normal_price"],
                product["discount_price"],
            )
    return await get_cart(pool, customer_id)


async def update_item(pool: asyncpg.Pool, customer_id: int, item_id: int, data: CartItemUpdate) -> dict:
    async with pool.acquire() as conn:
        cart = await _get_or_create_cart(conn, customer_id)
        result = await conn.execute(
            "UPDATE marketplace_cart_items SET quantity = $1 WHERE id = $2 AND cart_id = $3",
            data.quantity,
            item_id,
            cart["id"],
        )
    if result == "UPDATE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item cart tidak ditemukan")
    return await get_cart(pool, customer_id)


async def remove_item(pool: asyncpg.Pool, customer_id: int, item_id: int) -> None:
    async with pool.acquire() as conn:
        cart = await _get_or_create_cart(conn, customer_id)
        result = await conn.execute(
            "DELETE FROM marketplace_cart_items WHERE id = $1 AND cart_id = $2",
            item_id,
            cart["id"],
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item cart tidak ditemukan")

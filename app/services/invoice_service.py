import asyncpg
from fastapi import HTTPException, status

from app.schemas.invoice import InvoiceCreate


async def _generate_invoice_number(conn: asyncpg.Connection) -> str:
    """Format: INV-YYYYMMDD-#### (urut per hari)."""
    row = await conn.fetchrow(
        """
        SELECT 'INV-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
               LPAD((COUNT(*) + 1)::TEXT, 4, '0') AS invoice_number
        FROM invoices
        WHERE invoice_date = CURRENT_DATE
        """
    )
    return row["invoice_number"]


async def _fetch_invoice_with_items(conn: asyncpg.Connection, invoice_id: int) -> dict:
    invoice = await conn.fetchrow("SELECT * FROM invoices WHERE id = $1", invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice tidak ditemukan")
    items = await conn.fetch(
        "SELECT * FROM invoices_detail WHERE invoice_id = $1 ORDER BY id",
        invoice_id,
    )
    return {**dict(invoice), "items": [dict(i) for i in items]}


async def get_invoice(pool: asyncpg.Pool, invoice_id: int) -> dict:
    async with pool.acquire() as conn:
        return await _fetch_invoice_with_items(conn, invoice_id)


async def list_invoices(
    pool: asyncpg.Pool, status_filter: str | None, customer_id: int | None, limit: int, offset: int
) -> list[dict]:
    query = "SELECT * FROM invoices WHERE 1=1"
    params: list = []
    if status_filter:
        params.append(status_filter)
        query += f" AND status_transaksi = ${len(params)}"
    if customer_id:
        params.append(customer_id)
        query += f" AND customer_id = ${len(params)}"
    params.extend([limit, offset])
    query += f" ORDER BY id DESC LIMIT ${len(params) - 1} OFFSET ${len(params)}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


async def create_invoice(pool: asyncpg.Pool, data: InvoiceCreate) -> dict:
    """
    Membuat invoice + semua detail dalam SATU transaksi. Insert ke
    invoices_detail akan otomatis memicu trigger
    `trg_adjust_stock_on_invoice_detail` yang mengurangi stok produk.
    Kalau stok produk manapun tidak cukup, trigger akan RAISE EXCEPTION
    dan seluruh transaksi (termasuk invoice header) ikut di-rollback —
    jadi tidak mungkin ada invoice "setengah jadi".
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            customer = await conn.fetchrow("SELECT * FROM customers WHERE id = $1", data.customer_id)
            if customer is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer tidak ditemukan")

            if not data.items:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice harus punya minimal 1 item")

            subtotal_total = sum(
                (item.price_at_checkout - item.discount_price_at_checkout) * item.quantity
                for item in data.items
            )
            net_amount = subtotal_total - data.discount + data.vat + data.shipping_cost

            invoice_number = await _generate_invoice_number(conn)

            invoice = await conn.fetchrow(
                """
                INSERT INTO invoices (
                    invoice_number, customer_id, customer_name, customer_phone,
                    customer_email, customer_address, transaction_date, invoice_date,
                    shipping_date, total_amount, discount, vat, shipping_cost,
                    net_amount, sales_method
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                RETURNING *
                """,
                invoice_number,
                data.customer_id,
                customer["nama"],
                customer["telepon"],
                customer["email"],
                customer["alamat_domisili"],
                data.transaction_date,
                data.invoice_date,
                data.shipping_date,
                subtotal_total,
                data.discount,
                data.vat,
                data.shipping_cost,
                net_amount,
                data.sales_method,
            )

            for item in data.items:
                product = await conn.fetchrow(
                    "SELECT type, category FROM products WHERE id = $1",
                    item.product_id,
                )
                if product is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Produk id {item.product_id} tidak ditemukan",
                    )
                item_subtotal = (item.price_at_checkout - item.discount_price_at_checkout) * item.quantity
                product_name = product["type"] or product["category"] or f"Produk #{item.product_id}"

                # INSERT ini men-trigger fn_adjust_stock_on_invoice_detail
                # yang otomatis mengurangi stok & menolak kalau stok kurang.
                await conn.execute(
                    """
                    INSERT INTO invoices_detail (
                        invoice_id, product_id, product_name, quantity,
                        price_at_checkout, discount_price_at_checkout, subtotal
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7)
                    """,
                    invoice["id"],
                    item.product_id,
                    product_name,
                    item.quantity,
                    item.price_at_checkout,
                    item.discount_price_at_checkout,
                    item_subtotal,
                )

            return await _fetch_invoice_with_items(conn, invoice["id"])


async def update_invoice_status(pool: asyncpg.Pool, invoice_id: int, new_status: str) -> dict:
    async with pool.acquire() as conn:
        async with conn.transaction():
            if new_status == "dibatalkan":
                # Menghapus semua detail invoice akan otomatis
                # MENGEMBALIKAN stok lewat trigger yang sama.
                await conn.execute("DELETE FROM invoices_detail WHERE invoice_id = $1", invoice_id)

            result = await conn.execute(
                "UPDATE invoices SET status_transaksi = $1 WHERE id = $2",
                new_status,
                invoice_id,
            )
            if result == "UPDATE 0":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice tidak ditemukan")

            return await _fetch_invoice_with_items(conn, invoice_id)

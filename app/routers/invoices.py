import asyncpg
from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceStatusUpdate
from app.services import invoice_service

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=list[InvoiceOut])
async def list_invoices(
    status_transaksi: str | None = None,
    customer_id: int | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db),
):
    return await invoice_service.list_invoices(pool, status_transaksi, customer_id, limit, offset)


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(invoice_id: int, pool: asyncpg.Pool = Depends(get_db)):
    return await invoice_service.get_invoice(pool, invoice_id)


@router.post("", response_model=InvoiceOut, status_code=201)
async def create_invoice(payload: InvoiceCreate, pool: asyncpg.Pool = Depends(get_db)):
    """
    Membuat invoice baru. Stok setiap produk yang dipesan akan
    OTOMATIS BERKURANG (trigger database). Jika stok salah satu
    produk tidak cukup, seluruh invoice akan ditolak (400/409) dan
    tidak ada perubahan apa pun yang tersimpan.
    """
    return await invoice_service.create_invoice(pool, payload)


@router.patch("/{invoice_id}/status", response_model=InvoiceOut)
async def update_status(invoice_id: int, payload: InvoiceStatusUpdate, pool: asyncpg.Pool = Depends(get_db)):
    """
    Mengubah status invoice. Kalau diubah ke 'dibatalkan', stok produk
    yang tadinya dikurangi akan OTOMATIS DIKEMBALIKAN.
    """
    return await invoice_service.update_invoice_status(pool, invoice_id, payload.status_transaksi.value)

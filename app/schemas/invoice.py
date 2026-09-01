from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class StatusTransaksi(str, Enum):
    pesanan_baru = "pesanan_baru"
    diproses = "diproses"
    dikirim = "dikirim"
    selesai = "selesai"
    dibatalkan = "dibatalkan"


class InvoiceDetailCreate(BaseModel):
    product_id: int
    quantity: int
    price_at_checkout: Decimal
    discount_price_at_checkout: Decimal = Decimal("0")


class InvoiceCreate(BaseModel):
    customer_id: int
    invoice_date: date
    transaction_date: date | None = None
    shipping_date: date | None = None
    discount: Decimal = Decimal("0")
    vat: Decimal = Decimal("0")
    shipping_cost: Decimal = Decimal("0")
    sales_method: str
    items: list[InvoiceDetailCreate]


class InvoiceStatusUpdate(BaseModel):
    status_transaksi: StatusTransaksi


class InvoiceDetailOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price_at_checkout: Decimal
    discount_price_at_checkout: Decimal
    subtotal: Decimal


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    customer_phone: str | None
    customer_email: str | None
    customer_address: str | None
    transaction_date: date | None
    invoice_date: date
    shipping_date: date | None
    total_amount: Decimal
    discount: Decimal
    vat: Decimal
    shipping_cost: Decimal
    net_amount: Decimal
    status_transaksi: StatusTransaksi
    sales_method: str
    created_at: datetime
    updated_at: datetime
    items: list[InvoiceDetailOut] = []

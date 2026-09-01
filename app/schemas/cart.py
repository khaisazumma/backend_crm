from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_add: Decimal
    discount_price_at_add: Decimal | None
    added_at: datetime


class CartOut(BaseModel):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
    items: list[CartItemOut] = []

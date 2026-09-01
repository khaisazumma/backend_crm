import asyncpg
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartOut
from app.services import cart_service

router = APIRouter(prefix="/customers/{customer_id}/cart", tags=["Cart"])


@router.get("", response_model=CartOut)
async def get_cart(customer_id: int, pool: asyncpg.Pool = Depends(get_db)):
    return await cart_service.get_cart(pool, customer_id)


@router.post("/items", response_model=CartOut, status_code=201)
async def add_item(customer_id: int, payload: CartItemCreate, pool: asyncpg.Pool = Depends(get_db)):
    return await cart_service.add_item(pool, customer_id, payload)


@router.put("/items/{item_id}", response_model=CartOut)
async def update_item(
    customer_id: int, item_id: int, payload: CartItemUpdate, pool: asyncpg.Pool = Depends(get_db)
):
    return await cart_service.update_item(pool, customer_id, item_id, payload)


@router.delete("/items/{item_id}", status_code=204)
async def remove_item(customer_id: int, item_id: int, pool: asyncpg.Pool = Depends(get_db)):
    await cart_service.remove_item(pool, customer_id, item_id)

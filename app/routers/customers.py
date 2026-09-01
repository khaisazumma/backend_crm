import asyncpg
from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.customer import (
    CustomerCreate,
    CustomerListOut,
    CustomerOut,
    CustomerUpdate,
)
from app.services import customer_service

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=list[CustomerListOut])
async def list_customers(
    search: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db),
):
    return await customer_service.list_customers(pool, search, limit, offset)


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(customer_id: int, pool: asyncpg.Pool = Depends(get_db)):
    return await customer_service.get_customer(pool, customer_id)


@router.post("", response_model=CustomerOut, status_code=201)
async def create_customer(payload: CustomerCreate, pool: asyncpg.Pool = Depends(get_db)):
    return await customer_service.create_customer(pool, payload)


@router.put("/{customer_id}", response_model=CustomerOut)
async def update_customer(customer_id: int, payload: CustomerUpdate, pool: asyncpg.Pool = Depends(get_db)):
    return await customer_service.update_customer(pool, customer_id, payload)


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: int, pool: asyncpg.Pool = Depends(get_db)):
    await customer_service.delete_customer(pool, customer_id)

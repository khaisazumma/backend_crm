from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, model_validator


class ProductType(str, Enum):
    venjet = "venjet"
    blowerve = "blowerve"
    feederve = "feederve"
    kincirve = "kincirve"


class FeederveAttributes(BaseModel):
    version: str
    motor_type: str
    thrower: int
    measurer: str


class KincirveAttributes(BaseModel):
    version: str
    phase: int
    gearbox: bool
    material: str
    spline: int
    fan: int


class ProductCreate(BaseModel):
    product_type: ProductType
    type: str | None = None
    category: str | None = None
    description: str | None = None
    specification: str | None = None
    normal_price: Decimal
    discount_price: Decimal | None = None
    stock: int = 0
    sku: str | None = None

    # wajib diisi kalau product_type == feederve
    feederve_attributes: FeederveAttributes | None = None
    # wajib diisi kalau product_type == kincirve
    kincirve_attributes: KincirveAttributes | None = None

    @model_validator(mode="after")
    def validate_type_specific_attributes(self):
        if self.product_type == ProductType.feederve and self.feederve_attributes is None:
            raise ValueError("feederve_attributes wajib diisi untuk product_type='feederve'")
        if self.product_type == ProductType.kincirve and self.kincirve_attributes is None:
            raise ValueError("kincirve_attributes wajib diisi untuk product_type='kincirve'")
        return self


class ProductUpdate(BaseModel):
    """Update sebagian (field yang tidak dikirim / null tidak diubah)."""

    type: str | None = None
    category: str | None = None
    description: str | None = None
    specification: str | None = None
    normal_price: Decimal | None = None
    discount_price: Decimal | None = None
    stock: int | None = None
    is_active: bool | None = None
    feederve_attributes: FeederveAttributes | None = None
    kincirve_attributes: KincirveAttributes | None = None


class ProductOut(BaseModel):
    id: int
    product_type: ProductType
    sku: str | None
    type: str | None
    category: str | None
    description: str | None
    specification: str | None
    normal_price: Decimal
    discount_price: Decimal | None
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    feederve_attributes: FeederveAttributes | None = None
    kincirve_attributes: KincirveAttributes | None = None

class ProductListOut(BaseModel):
    id: int
    product_type: ProductType
    sku: str | None
    product: str | None
    category: str | None
    normal_price: Decimal
    discount_price: Decimal | None
    price: Decimal
    stock: int
    is_active: bool
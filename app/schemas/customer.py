from datetime import datetime

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    nama: str
    gender: str | None = None
    email: EmailStr | None = None
    telepon: str | None = None
    alamat_domisili: str | None = None
    alamat_usaha: str | None = None
    provinsi: str | None = None
    kabupaten_kota: str | None = None
    kecamatan: str | None = None
    kelurahan_desa: str | None = None
    jenis_peternak: str | None = None
    komoditas: str | None = None
    luas_tambak: str | None = None
    teknologi: str | None = None
    padat_tebar: str | None = None


class CustomerUpdate(BaseModel):
    nama: str | None = None
    gender: str | None = None
    email: EmailStr | None = None
    telepon: str | None = None
    alamat_domisili: str | None = None
    alamat_usaha: str | None = None
    provinsi: str | None = None
    kabupaten_kota: str | None = None
    kecamatan: str | None = None
    kelurahan_desa: str | None = None
    jenis_peternak: str | None = None
    komoditas: str | None = None
    luas_tambak: str | None = None
    teknologi: str | None = None
    padat_tebar: str | None = None


class CustomerOut(BaseModel):
    id: int
    id_client: int
    nama: str
    gender: str | None
    email: str | None
    telepon: str | None
    alamat_domisili: str | None
    alamat_usaha: str | None
    provinsi: str | None
    kabupaten_kota: str | None
    kecamatan: str | None
    kelurahan_desa: str | None
    jenis_peternak: str | None
    komoditas: str | None
    luas_tambak: str | None
    teknologi: str | None
    padat_tebar: str | None
    created_at: datetime
    updated_at: datetime

class CustomerListOut(BaseModel):
    id: int
    id_client: int
    nama: str
    email: str | None
    telepon: str | None
    provinsi: str | None
    kabupaten_kota: str | None
    komoditas: str | None
    luas_tambak: str | None
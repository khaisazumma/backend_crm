# Venambak CRM — Backend API

Backend FastAPI untuk Venambak CRM. Tidak pakai ORM — semua query ke
database ditulis sebagai SQL mentah dengan **asyncpg**, memanggil
tabel/fungsi/trigger dari `venambak_schema_fix.sql`.

## Struktur Folder

```
app/
  core/
    config.py        # baca .env
    database.py       # connection pool asyncpg
    security.py        # hashing password (bcrypt) + JWT
    dependencies.py     # dependency ambil admin login dari token
  schemas/            # Pydantic request/response tiap modul
  services/           # SQL mentah (query, insert, update) tiap modul
  routers/            # endpoint FastAPI tiap modul
  main.py             # entry point, daftar semua router
requirements.txt
.env.example
```

## Setup

1. Buat & aktifkan virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

2. Install dependency:
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan dulu `venambak_schema_fix.sql`** ke database
   `venambak_crm` Anda (lewat `psql` atau tool database favorit Anda)
   kalau belum pernah dijalankan. File itu sekarang ada 1 baris admin
   dengan `password_hash` placeholder — generate hash asli dulu:
   ```bash
   python3 -c "from passlib.context import CryptContext; \
       ctx = CryptContext(schemes=['bcrypt']); \
       print(ctx.hash('PASSWORD_ANDA'))"
   ```
   lalu:
   ```sql
   UPDATE admins SET password_hash = '<hasil hash di atas>'
   WHERE email = 'admin@venambak.com';
   ```

4. Salin `.env.example` jadi `.env`, isi kredensial database & JWT
   secret Anda.

5. Jalankan server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. Buka dokumentasi API interaktif (Swagger) di:
   `http://localhost:8000/docs`

## Login

```
POST /auth/login
{
  "email": "admin@venambak.com",
  "password": "PASSWORD_ANDA"
}
```

Response berisi `access_token` — pakai sebagai header
`Authorization: Bearer <access_token>` untuk semua endpoint yang
butuh login (customers, products create/update/delete, invoices,
commissions).

## Alur Stok Otomatis

- Endpoint `POST /invoices` membuat invoice + detail dalam satu
  transaksi database. Trigger `trg_adjust_stock_on_invoice_detail` di
  database otomatis **mengurangi** `products.stock` untuk tiap item.
- Kalau stok produk manapun tidak cukup, trigger menolak (RAISE
  EXCEPTION) dan **seluruh invoice ikut dibatalkan** (rollback) — tidak
  ada invoice "setengah jadi".
- Endpoint `PATCH /invoices/{id}/status` dengan status `dibatalkan`
  akan menghapus detail invoice, yang otomatis **mengembalikan** stok.

## Endpoint Utama

| Modul      | Endpoint                                   | Perlu Login |
|------------|---------------------------------------------|-------------|
| Auth       | `POST /auth/login`                          | tidak       |
| Auth       | `POST /auth/admins`                         | SUPER_ADMIN |
| Customers  | CRUD `/customers`                           | ya          |
| Products   | `GET /products` (katalog)                   | tidak       |
| Products   | `POST/PUT /products` (tambah/edit)          | ADMIN+      |
| Products   | `DELETE /products/{id}` (hapus permanen)    | SUPER_ADMIN |
| Products   | `PATCH /products/{id}/deactivate`           | ADMIN+      |
| Cart       | CRUD `/customers/{id}/cart`                 | tidak       |
| Invoices   | CRUD `/invoices`                            | ya          |
| Commissions| `GET /commissions`                          | ya          |

## Menghubungkan ke Frontend

Set `CORS_ORIGINS` di `.env` sesuai alamat dev-server frontend Anda
(misalnya `http://localhost:5173` untuk Vite, `http://localhost:3000`
untuk Next.js/CRA).

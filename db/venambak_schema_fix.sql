-- =====================================================================
-- VENAMBAK CRM — SQL SCHEMA FINAL (FIXED & TERINTEGRASI)
-- Target   : database "venambak_crm", user "venambak"
-- Postgres : 16.15
--
-- PERUBAHAN UTAMA DARI VERSI SEBELUMNYA:
--   1. Tabel produk (venjet/blowerve/feederve/kincirve) disatukan ke
--      induk "products" (+ tabel anak untuk field khusus feederve &
--      kincirve). Ini yang memungkinkan:
--        - 1 tabel untuk CRUD produk (tambah/edit/hapus/lihat)
--        - FK yang benar dari invoices_detail & cart_items ke produk
--        - Stok otomatis berkurang saat invoice masuk (trigger)
--   2. invoices_detail & marketplace_cart_items sekarang punya
--      product_id yang FK ke products(id) — sebelumnya polos/tanpa FK.
--   3. Ditambahkan fungsi CRUD (PL/pgSQL) untuk products & customers.
--   4. Ditambahkan 1 akun admin siap pakai (lihat catatan password
--      di bagian paling bawah SEBELUM dijalankan).
--
-- Aman dijalankan ulang (IF NOT EXISTS) & atomik (BEGIN...COMMIT).
-- TIDAK men-drop tabel/data yang sudah ada.
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. ADMINS
-- =====================================================================
CREATE TABLE IF NOT EXISTS admins (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(50) NOT NULL
                        CHECK (role IN ('SUPER_ADMIN', 'ADMIN', 'SALES')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- =====================================================================
-- 2. CUSTOMERS
-- =====================================================================
CREATE TABLE IF NOT EXISTS customers (
    id                  SERIAL PRIMARY KEY,
    id_client           INTEGER NOT NULL UNIQUE,
    nama                TEXT NOT NULL,
    gender              TEXT,
    email               TEXT,
    telepon             TEXT UNIQUE,
    alamat_domisili     TEXT,
    alamat_usaha        TEXT,
    provinsi            TEXT,
    kabupaten_kota      TEXT,
    kecamatan           TEXT,
    kelurahan_desa      TEXT,
    jenis_peternak      TEXT,
    komoditas           TEXT,
    luas_tambak         TEXT,
    teknologi           TEXT,
    padat_tebar         TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- 3. SALES TEAM
-- =====================================================================
CREATE TABLE IF NOT EXISTS sales_team (
    id                  SERIAL PRIMARY KEY,
    nama_sales          VARCHAR(100) NOT NULL UNIQUE,
    tipe_sales          VARCHAR(50) NOT NULL,
    komisi_percentage   NUMERIC(5,2) NOT NULL DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE
);

-- =====================================================================
-- 4. PRODUCTS (TABEL INDUK — SATU TABEL UNTUK SEMUA JENIS PRODUK)
--    product_type membedakan venjet / blowerve / feederve / kincirve.
--    Semua field yang common (harga, stok, aktif/tidak) ada di sini
--    sehingga CRUD & update stok cukup lewat 1 tabel.
-- =====================================================================
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    product_type    VARCHAR(20) NOT NULL
                        CHECK (product_type IN ('venjet','blowerve','feederve','kincirve')),
    sku             TEXT UNIQUE,
    type            VARCHAR(50),
    category        VARCHAR(100),
    description     TEXT,
    specification   TEXT,
    normal_price    NUMERIC(15,2) NOT NULL CHECK (normal_price >= 0),
    discount_price  NUMERIC(15,2) CHECK (discount_price IS NULL OR discount_price >= 0),
    stock           INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Field khusus FEEDERVE (relasi 1-1 ke products)
CREATE TABLE IF NOT EXISTS feederve_attributes (
    product_id      INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    version         VARCHAR(20) NOT NULL,
    motor_type      VARCHAR(10) NOT NULL,
    thrower         INTEGER NOT NULL,
    measurer        VARCHAR(20) NOT NULL
);

-- Field khusus KINCIRVE (relasi 1-1 ke products)
CREATE TABLE IF NOT EXISTS kincirve_attributes (
    product_id      INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    version         VARCHAR(20) NOT NULL,
    phase           INTEGER NOT NULL,
    gearbox         BOOLEAN NOT NULL,
    material        VARCHAR(20) NOT NULL,
    spline          INTEGER NOT NULL,
    fan             INTEGER NOT NULL
);

-- View bantu supaya query "produk lengkap per jenis" gampang dari backend
CREATE OR REPLACE VIEW v_products_full AS
SELECT
    p.*,
    fa.version   AS feederve_version,
    fa.motor_type AS feederve_motor_type,
    fa.thrower   AS feederve_thrower,
    fa.measurer  AS feederve_measurer,
    ka.version   AS kincirve_version,
    ka.phase     AS kincirve_phase,
    ka.gearbox   AS kincirve_gearbox,
    ka.material  AS kincirve_material,
    ka.spline    AS kincirve_spline,
    ka.fan       AS kincirve_fan
FROM products p
LEFT JOIN feederve_attributes fa ON fa.product_id = p.id AND p.product_type = 'feederve'
LEFT JOIN kincirve_attributes ka ON ka.product_id = p.id AND p.product_type = 'kincirve';

-- =====================================================================
-- 5. MARKETPLACE CART
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketplace_cart (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- 6. MARKETPLACE CART ITEMS — product_id sekarang FK ke products(id)
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketplace_cart_items (
    id                          SERIAL PRIMARY KEY,
    cart_id                     INTEGER NOT NULL REFERENCES marketplace_cart(id) ON DELETE CASCADE,
    product_id                  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity                    INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    price_at_add                NUMERIC(12,2) NOT NULL,
    discount_price_at_add       NUMERIC(12,2),
    added_at                    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- 7. INVOICES
-- =====================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id                  SERIAL PRIMARY KEY,
    invoice_number      TEXT NOT NULL UNIQUE,
    customer_id         INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    customer_name       TEXT NOT NULL,
    customer_phone      TEXT,
    customer_email      TEXT,
    customer_address    TEXT,

    transaction_date    DATE,
    invoice_date        DATE NOT NULL,
    shipping_date       DATE,

    total_amount        NUMERIC(14,2) NOT NULL,
    discount            NUMERIC(14,2) NOT NULL DEFAULT 0,
    vat                 NUMERIC(14,2) NOT NULL DEFAULT 0,
    shipping_cost       NUMERIC(14,2) NOT NULL DEFAULT 0,
    net_amount          NUMERIC(14,2) NOT NULL,

    status_transaksi    TEXT NOT NULL DEFAULT 'pesanan_baru'
                            CHECK (status_transaksi IN ('pesanan_baru','diproses','dikirim','selesai','dibatalkan')),

    sales_method        TEXT NOT NULL,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- 8. INVOICES DETAIL — product_id sekarang WAJIB & FK ke products(id).
--    Inilah yang dipakai trigger untuk mengurangi stok otomatis.
--    product_name & price_at_checkout tetap disimpan sebagai snapshot
--    historis (kalau harga/nama produk berubah nanti, invoice lama
--    tidak ikut berubah).
-- =====================================================================
CREATE TABLE IF NOT EXISTS invoices_detail (
    id                          SERIAL PRIMARY KEY,
    invoice_id                  INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id                  INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_name                TEXT NOT NULL,
    quantity                    INTEGER NOT NULL CHECK (quantity > 0),
    price_at_checkout           NUMERIC(14,2) NOT NULL,
    discount_price_at_checkout  NUMERIC(14,2) NOT NULL DEFAULT 0,
    subtotal                    NUMERIC(14,2) NOT NULL
);

-- =====================================================================
-- 9. INVOICE SHIPMENTS
-- =====================================================================
CREATE TABLE IF NOT EXISTS invoice_shipments (
    id              SERIAL PRIMARY KEY,
    invoice_id      INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    no_resi         TEXT NOT NULL,
    shipping_date   DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- 10. COMMISSIONS
-- =====================================================================
CREATE TABLE IF NOT EXISTS commissions (
    id                  SERIAL PRIMARY KEY,
    sales_id            INTEGER REFERENCES sales_team(id) ON DELETE SET NULL,
    order_id            INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    amount_komisi       NUMERIC(15,2) NOT NULL DEFAULT 0,
    status_komisi       VARCHAR(20) NOT NULL DEFAULT 'Belum dicairkan',
    tanggal_pencairan   DATE,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- TRIGGER: auto-update updated_at
-- =====================================================================
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_invoices_updated_at ON invoices;
CREATE TRIGGER trg_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_marketplace_cart_updated_at ON marketplace_cart;
CREATE TRIGGER trg_marketplace_cart_updated_at
    BEFORE UPDATE ON marketplace_cart
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_products_updated_at ON products;
CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers;
CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- =====================================================================
-- TRIGGER: STOK OTOMATIS BERKURANG / BERTAMBAH SAAT INVOICE DETAIL
-- BERUBAH (INSERT = stok berkurang, DELETE = stok dikembalikan,
-- UPDATE quantity/product_id = disesuaikan selisihnya).
-- Jika stok tidak cukup, transaksi DITOLAK (RAISE EXCEPTION) supaya
-- stok tidak pernah minus.
-- =====================================================================
CREATE OR REPLACE FUNCTION fn_adjust_stock_on_invoice_detail()
RETURNS TRIGGER AS $$
DECLARE
    v_current_stock INTEGER;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT stock INTO v_current_stock FROM products WHERE id = NEW.product_id FOR UPDATE;
        IF v_current_stock IS NULL THEN
            RAISE EXCEPTION 'Produk id % tidak ditemukan', NEW.product_id;
        END IF;
        IF v_current_stock < NEW.quantity THEN
            RAISE EXCEPTION 'Stok produk id % tidak cukup (tersedia %, diminta %)',
                NEW.product_id, v_current_stock, NEW.quantity;
        END IF;
        UPDATE products SET stock = stock - NEW.quantity WHERE id = NEW.product_id;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE products SET stock = stock + OLD.quantity WHERE id = OLD.product_id;
        RETURN OLD;

    ELSIF TG_OP = 'UPDATE' THEN
        -- kembalikan stok lama dulu, lalu kurangi sesuai quantity baru
        UPDATE products SET stock = stock + OLD.quantity WHERE id = OLD.product_id;

        SELECT stock INTO v_current_stock FROM products WHERE id = NEW.product_id FOR UPDATE;
        IF v_current_stock IS NULL THEN
            RAISE EXCEPTION 'Produk id % tidak ditemukan', NEW.product_id;
        END IF;
        IF v_current_stock < NEW.quantity THEN
            RAISE EXCEPTION 'Stok produk id % tidak cukup (tersedia %, diminta %)',
                NEW.product_id, v_current_stock, NEW.quantity;
        END IF;
        UPDATE products SET stock = stock - NEW.quantity WHERE id = NEW.product_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_adjust_stock_on_invoice_detail ON invoices_detail;
CREATE TRIGGER trg_adjust_stock_on_invoice_detail
    AFTER INSERT OR UPDATE OF quantity, product_id OR DELETE ON invoices_detail
    FOR EACH ROW EXECUTE FUNCTION fn_adjust_stock_on_invoice_detail();

-- =====================================================================
-- FUNGSI CRUD: PRODUCTS
-- =====================================================================

-- CREATE
CREATE OR REPLACE FUNCTION fn_product_create(
    p_product_type   VARCHAR,
    p_type           VARCHAR,
    p_category       VARCHAR,
    p_description    TEXT,
    p_specification  TEXT,
    p_normal_price   NUMERIC,
    p_stock          INTEGER,
    p_sku            TEXT DEFAULT NULL,
    p_discount_price NUMERIC DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO products (product_type, type, category, description, specification,
                           normal_price, discount_price, stock, sku)
    VALUES (p_product_type, p_type, p_category, p_description, p_specification,
            p_normal_price, p_discount_price, p_stock, p_sku)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- UPDATE (partial update: kirim NULL untuk field yang tidak ingin diubah)
CREATE OR REPLACE FUNCTION fn_product_update(
    p_id             INTEGER,
    p_type           VARCHAR DEFAULT NULL,
    p_category       VARCHAR DEFAULT NULL,
    p_description    TEXT DEFAULT NULL,
    p_specification  TEXT DEFAULT NULL,
    p_normal_price   NUMERIC DEFAULT NULL,
    p_discount_price NUMERIC DEFAULT NULL,
    p_stock          INTEGER DEFAULT NULL,
    p_is_active      BOOLEAN DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE products SET
        type           = COALESCE(p_type, type),
        category       = COALESCE(p_category, category),
        description    = COALESCE(p_description, description),
        specification  = COALESCE(p_specification, specification),
        normal_price   = COALESCE(p_normal_price, normal_price),
        discount_price = COALESCE(p_discount_price, discount_price),
        stock          = COALESCE(p_stock, stock),
        is_active      = COALESCE(p_is_active, is_active)
    WHERE id = p_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- DELETE (soft delete supaya histori invoice tidak rusak — set nonaktif)
CREATE OR REPLACE FUNCTION fn_product_deactivate(p_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE products SET is_active = FALSE WHERE id = p_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- DELETE PERMANEN (hanya berhasil kalau produk belum pernah dipakai di invoice manapun)
CREATE OR REPLACE FUNCTION fn_product_delete_hard(p_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM products WHERE id = p_id;
    RETURN FOUND;
EXCEPTION WHEN foreign_key_violation THEN
    RAISE EXCEPTION 'Produk id % sudah pernah dipakai di invoice, tidak bisa dihapus permanen. Gunakan fn_product_deactivate.', p_id;
END;
$$ LANGUAGE plpgsql;

-- READ (satu produk, lengkap dengan atribut khusus)
CREATE OR REPLACE FUNCTION fn_product_get(p_id INTEGER)
RETURNS SETOF v_products_full AS $$
    SELECT * FROM v_products_full WHERE id = p_id;
$$ LANGUAGE sql STABLE;

-- =====================================================================
-- FUNGSI CRUD: CUSTOMERS
-- =====================================================================

CREATE OR REPLACE FUNCTION fn_customer_create(
    p_id_client       INTEGER,
    p_nama            TEXT,
    p_gender          TEXT DEFAULT NULL,
    p_email           TEXT DEFAULT NULL,
    p_telepon         TEXT DEFAULT NULL,
    p_alamat_domisili TEXT DEFAULT NULL,
    p_alamat_usaha    TEXT DEFAULT NULL,
    p_provinsi        TEXT DEFAULT NULL,
    p_kabupaten_kota  TEXT DEFAULT NULL,
    p_kecamatan       TEXT DEFAULT NULL,
    p_kelurahan_desa  TEXT DEFAULT NULL,
    p_jenis_peternak  TEXT DEFAULT NULL,
    p_komoditas       TEXT DEFAULT NULL,
    p_luas_tambak     TEXT DEFAULT NULL,
    p_teknologi       TEXT DEFAULT NULL,
    p_padat_tebar     TEXT DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO customers (id_client, nama, gender, email, telepon, alamat_domisili,
                            alamat_usaha, provinsi, kabupaten_kota, kecamatan, kelurahan_desa,
                            jenis_peternak, komoditas, luas_tambak, teknologi, padat_tebar)
    VALUES (p_id_client, p_nama, p_gender, p_email, p_telepon, p_alamat_domisili,
            p_alamat_usaha, p_provinsi, p_kabupaten_kota, p_kecamatan, p_kelurahan_desa,
            p_jenis_peternak, p_komoditas, p_luas_tambak, p_teknologi, p_padat_tebar)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_customer_update(
    p_id              INTEGER,
    p_nama            TEXT DEFAULT NULL,
    p_gender          TEXT DEFAULT NULL,
    p_email           TEXT DEFAULT NULL,
    p_telepon         TEXT DEFAULT NULL,
    p_alamat_domisili TEXT DEFAULT NULL,
    p_alamat_usaha    TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE customers SET
        nama            = COALESCE(p_nama, nama),
        gender          = COALESCE(p_gender, gender),
        email           = COALESCE(p_email, email),
        telepon         = COALESCE(p_telepon, telepon),
        alamat_domisili = COALESCE(p_alamat_domisili, alamat_domisili),
        alamat_usaha    = COALESCE(p_alamat_usaha, alamat_usaha)
    WHERE id = p_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_customer_delete(p_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM customers WHERE id = p_id;
    RETURN FOUND;
EXCEPTION WHEN foreign_key_violation THEN
    RAISE EXCEPTION 'Customer id % masih punya invoice/cart terkait, tidak bisa dihapus.', p_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- INDEX
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status_transaksi);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_detail_invoice_id ON invoices_detail(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoices_detail_product_id ON invoices_detail(product_id);
CREATE INDEX IF NOT EXISTS idx_invoice_shipments_invoice_id ON invoice_shipments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_cart_customer_id ON marketplace_cart(customer_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_cart_items_cart_id ON marketplace_cart_items(cart_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_cart_items_product_id ON marketplace_cart_items(product_id);
CREATE INDEX IF NOT EXISTS idx_commissions_sales_id ON commissions(sales_id);
CREATE INDEX IF NOT EXISTS idx_commissions_order_id ON commissions(order_id);
CREATE INDEX IF NOT EXISTS idx_customers_id_client ON customers(id_client);
CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);

-- =====================================================================
-- SEED: 1 AKUN ADMIN SIAP PAKAI
--
-- !!! PENTING — BACA SEBELUM MENJALANKAN !!!
-- password_hash di bawah ini BUKAN hash asli, hanya placeholder teks
-- 'GANTI_DENGAN_HASH_ASLI' karena environment saya tidak punya akses
-- internet/library bcrypt untuk generate hash yang valid buat backend
-- Anda. Backend Anda (FastAPI) kemungkinan verifikasi password pakai
-- bcrypt/passlib, jadi WAJIB diganti sebelum bisa dipakai login.
--
-- Cara generate hash yang benar (jalankan di server/komputer yang
-- sudah punya library backend Anda, misalnya lewat python3 -c):
--
--   pip install passlib[bcrypt]
--   python3 -c "from passlib.context import CryptContext; \
--       ctx = CryptContext(schemes=['bcrypt']); \
--       print(ctx.hash('PASSWORD_ANDA_DI_SINI'))"
--
-- Lalu tempel hasilnya menggantikan 'GANTI_DENGAN_HASH_ASLI' di bawah,
-- atau jalankan UPDATE setelah INSERT ini.
-- =====================================================================
INSERT INTO admins (email, password_hash, role, is_active)
VALUES ('admin@venambak.com', 'GANTI_DENGAN_HASH_ASLI', 'SUPER_ADMIN', TRUE)
ON CONFLICT (email) DO NOTHING;

COMMIT;

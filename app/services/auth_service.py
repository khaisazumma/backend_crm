import asyncpg
from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password


async def authenticate_admin(pool: asyncpg.Pool, email: str, password: str) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, password_hash, role, is_active, created_at
            FROM admins
            WHERE email = $1
            """,
            email,
        )

    if row is None or not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )

    if not verify_password(password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )

    token = create_access_token(
        {"sub": str(row["id"]), "email": row["email"], "role": row["role"]}
    )
    return {
        "access_token": token,
"admin": {
    "id": row["id"],
    "email": row["email"],
    "role": row["role"],
    "is_active": row["is_active"],
    "created_at": row["created_at"],
},
    }


async def create_admin(pool: asyncpg.Pool, email: str, password: str, role: str) -> dict:
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO admins (email, password_hash, role)
                VALUES ($1, $2, $3)
                RETURNING id, email, role, is_active, created_at
                """,
                email,
                hash_password(password),
                role,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email admin sudah terdaftar",
            )
    return dict(row)

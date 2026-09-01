"""
Dependency: ambil admin yang sedang login dari Authorization: Bearer <token>,
dan helper untuk membatasi endpoint hanya bisa diakses role tertentu.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa",
        )
    return {
        "id": int(payload.get("sub")),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }


def require_role(*allowed_roles: str):
    """
    Pemakaian di router: Depends(require_role("SUPER_ADMIN", "ADMIN"))
    """

    async def checker(admin: dict = Depends(get_current_admin)) -> dict:
        if admin["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak punya izin untuk mengakses resource ini",
            )
        return admin

    return checker

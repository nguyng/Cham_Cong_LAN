import ipaddress
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_token, hash_token
from app.database.session import get_db
from app.models.entities import LoginSession, RoleName, User

Db = Annotated[Session, Depends(get_db)]


def client_ip(request: Request) -> str:
    # Chỉ tin địa chỉ kết nối do ASGI server cung cấp. Reverse proxy phải được cấu hình
    # trusted proxy ở Uvicorn, không đọc X-Forwarded-For tùy ý.
    host = request.client.host if request.client else "0.0.0.0"
    if get_settings().environment == "test" and host == "testclient":
        return "127.0.0.1"
    return host


def require_lan(ip: str):
    address = ipaddress.ip_address(ip)
    if not any(address in ipaddress.ip_network(network) for network in get_settings().allowed_networks):
        raise HTTPException(403, "Địa chỉ IP không thuộc mạng nội bộ được phép")


def current_user(
    db: Db,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Thiếu access token", headers={"WWW-Authenticate": "Bearer"})
    token = authorization[7:]
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        session_id = payload["sid"]
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Access token không hợp lệ") from None
    session = db.scalar(
        select(LoginSession).where(
            LoginSession.id == session_id,
            LoginSession.user_id == user_id,
            LoginSession.token_hash == hash_token(token),
            LoginSession.revoked_at.is_(None),
        )
    )
    now = datetime.now(UTC)
    if not session or session.expires_at.replace(tzinfo=UTC) <= now:
        raise HTTPException(401, "Phiên đăng nhập đã hết hạn")
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(401, "Tài khoản không hoạt động")
    session.last_seen_at = now
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_roles(*roles: RoleName):
    def dependency(user: CurrentUser) -> User:
        if user.role.name not in roles:
            raise HTTPException(403, "Không có quyền thực hiện chức năng này")
        return user

    return dependency


Admin = Annotated[User, Depends(require_roles(RoleName.ADMIN))]
Manager = Annotated[User, Depends(require_roles(RoleName.ADMIN, RoleName.MANAGER))]

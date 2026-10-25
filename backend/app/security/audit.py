from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.security.models import AuditLog


# zapisuje zdarzenie bezpieczenstwa (commit robi wywolujacy)
def audit(db: AsyncSession, request: Request, user: User, action: str, detail: str = "") -> None:
    db.add(
        AuditLog(
            userId=user.id,
            action=action,
            detail=detail[:200],
            ip=request.client.host if request.client else "",
            userAgent=request.headers.get("user-agent", "")[:300],
        )
    )

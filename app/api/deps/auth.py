from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import verify_token
from app.models.user import User
from app.models.squad import UserRole, ROLE_LEVELS
from app.core.logging_config import get_logger

security = HTTPBearer()
logger = get_logger(__name__)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Verify JWT token and return current user"""
    try:
        token = credentials.credentials
        logger.info("Attempting to verify token", token_prefix=token[:20] if token else None)

        payload = verify_token(token)
        logger.info("Token verification result", payload=payload)

        if not payload or payload.get("type") != "access":
            logger.warning("Invalid token payload or wrong token type", payload=payload)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str = payload.get("sub")
        logger.info("Extracted user_id from token", user_id_str=user_id_str)

        if user_id_str is None:
            logger.warning("No user_id in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            logger.warning("Invalid user_id format in token", user_id_str=user_id_str)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        logger.info("Database lookup result", user_found=user is not None, user_active=user.is_active if user else None)

        if user is None or not user.is_active:
            logger.warning("User not found or inactive", user_id=user_id, user_exists=user is not None)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        logger.info("Authentication successful", user_id=user.id, username=user.username)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_current_user", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Return user if authenticated, None otherwise"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# =====================================================
# RBAC DEPENDENCIES
# =====================================================

def _role_level(role_value) -> int:
    """Resolve a role (str | UserRole) to its numeric privilege level."""
    key = role_value.value if isinstance(role_value, UserRole) else role_value
    return ROLE_LEVELS.get(key, 0)


def require_role(min_role: str) -> Callable:
    """Dependency factory: require the current user to have at least ``min_role``.

    Access is granted to ``min_role`` AND every more powerful role
    (e.g. ``require_role("qa_lead")`` admits qa_lead, kabag and admin).

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def handler(current_user: User = Depends(require_role("admin"))):
            ...
    """
    required_level = ROLE_LEVELS[min_role]

    async def _checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_level = _role_level(current_user.role)
        if user_level < required_level:
            logger.warning(
                "RBAC denied",
                user_id=current_user.id,
                user_role=current_user.role,
                required_role=min_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{min_role}' or higher",
            )
        return current_user

    _checker.__name__ = f"require_{min_role}"
    return _checker


async def get_data_scope(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[bool, Optional[List[int]]]:
    """Resolve which user_ids the current user is allowed to see data for.

    Returns ``(scope_all, user_ids)`` where:
    - ``scope_all=True,  user_ids=None``  → see everyone (kabag, admin)
    - ``scope_all=False, user_ids=[...]`` → only the listed user_ids

    qa_staff  → only themselves
    qa_lead   → all members of their squad (including themselves)
    kabag/admin → everyone
    """
    level = _role_level(current_user.role)

    if level >= ROLE_LEVELS["kabag"]:
        return (True, None)

    if level >= ROLE_LEVELS["qa_lead"]:
        # All members of the lead's squad (includes self)
        if current_user.squad_id is None:
            return (False, [current_user.id])
        result = await db.execute(
            select(User.id).where(User.squad_id == current_user.squad_id)
        )
        member_ids = [row[0] for row in result.all()]
        if current_user.id not in member_ids:
            member_ids.append(current_user.id)
        return (False, member_ids)

    # qa_staff
    return (False, [current_user.id])


async def can_access_session(
    session_user_id: int,
    current_user: User,
    db: AsyncSession,
) -> bool:
    """Check whether ``current_user`` may read/modify a session owned by
    ``session_user_id``. Respects role + squad scoping."""
    if current_user.id == session_user_id:
        return True

    level = _role_level(current_user.role)
    if level >= ROLE_LEVELS["kabag"]:
        return True
    if level >= ROLE_LEVELS["qa_lead"] and current_user.squad_id is not None:
        result = await db.execute(
            select(User.id).where(
                User.squad_id == current_user.squad_id,
                User.id == session_user_id,
            )
        )
        return result.scalar_one_or_none() is not None
    return False

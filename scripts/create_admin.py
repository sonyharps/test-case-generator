#!/usr/bin/env python
"""Bootstrap the first admin user (or promote an existing one).

Usage:
    python scripts/create_admin.py <username> <email> <password>

Creates a new user with role=admin, or — if the username/email already
exists — promotes the existing user to admin and (re)sets their password
& active status. Idempotent.
"""
import sys
import asyncio
from pathlib import Path

# Ensure project root is importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.core.security import hash_password  # noqa: E402


async def main(username: str, email: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
                is_active=True,
                role=UserRole.ADMIN,
            )
            db.add(user)
            action = "Created"
        else:
            user.role = UserRole.ADMIN
            user.hashed_password = hash_password(password)
            user.is_active = True
            action = "Promoted"

        await db.commit()
        print(f"{action} admin user '{username}' (id={user.id}, email={user.email}).")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/create_admin.py <username> <email> <password>")
        sys.exit(1)

    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))

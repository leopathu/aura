"""Repository for User database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Handles all User database queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, email: str, hashed_password: str) -> User:
        """Persist a new user and return it."""
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by their email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by their UUID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

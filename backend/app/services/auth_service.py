"""Authentication service — register, login."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuraException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, UserCreate, UserLogin


class AuthService:
    """Handles user registration and login."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def register(self, payload: UserCreate) -> User:
        """Create a new user account.

        Args:
            payload: Registration data (email + password).

        Returns:
            The newly created User instance.

        Raises:
            AuraException: If the email is already registered.
        """
        existing = await self._repo.get_by_email(payload.email)
        if existing:
            raise AuraException(
                detail="A user with this email already exists.",
                code="EMAIL_TAKEN",
            )
        hashed = hash_password(payload.password)
        return await self._repo.create(email=payload.email, hashed_password=hashed)

    async def login(self, payload: UserLogin) -> Token:
        """Authenticate a user and return a JWT token.

        Args:
            payload: Login credentials (email + password).

        Returns:
            A Token containing the signed JWT.

        Raises:
            AuraException: If credentials are invalid.
        """
        user = await self._repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise AuraException(
                detail="Invalid email or password.",
                code="INVALID_CREDENTIALS",
            )
        if not user.is_active:
            raise AuraException(detail="Account is inactive.", code="INACTIVE_USER")

        token = create_access_token(subject=str(user.id))
        return Token(access_token=token)

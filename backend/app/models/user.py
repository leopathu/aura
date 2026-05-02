"""ORM model for application users."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """Represents a registered user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    brains: Mapped[list["Brain"]] = relationship(  # noqa: F821
        "Brain", back_populates="user", cascade="all, delete-orphan"
    )
    ai_settings: Mapped["AISettings | None"] = relationship(  # noqa: F821
        "AISettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

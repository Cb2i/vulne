from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.READONLY)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped["Team"] = relationship(back_populates="users")

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="team")
    assets: Mapped[list["Asset"]] = relationship(back_populates="team")
    ownership_rules: Mapped[list["OwnershipRule"]] = relationship(back_populates="team")

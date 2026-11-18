from sqlalchemy import (
    String,
    ForeignKey,
    CheckConstraint
)

from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class Correo(Base):
    __tablename__ = "correos"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    id_priv_usuario: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "usuarios.id_priv",
            name="fk_correos_usuario",
            ondelete="CASCADE"
        ),
        nullable=True,
        unique=True
    )

    id_priv_admin: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "administradores.id_priv",
            name="fk_correos_admin",
            ondelete="CASCADE"
        ),
        nullable=True,
        unique=True
    )

    correo: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
        unique=True
    )

    __table_args__ = (
        CheckConstraint(
            "("
            "id_priv_usuario IS NOT NULL AND id_priv_admin IS NULL"
            ") OR ("
            "id_priv_usuario IS NULL AND id_priv_admin IS NOT NULL"
            ")",
            name="chk_correos_propietario"
        ),
    )
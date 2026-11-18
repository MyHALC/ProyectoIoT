from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    CheckConstraint,
    text
)

from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class Contrasena(Base):
    __tablename__ = "contrasenas"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    id_priv_usuario: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "usuarios.id_priv",
            name="fk_contrasenas_usuario",
            ondelete="CASCADE"
        ),
        nullable=True,
        unique=True
    )

    id_priv_admin: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "administradores.id_priv",
            name="fk_contrasenas_admin",
            ondelete="CASCADE"
        ),
        nullable=True,
        unique=True
    )

    contrasena: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    contra_cambiada: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0")
    )

    llave_hmac_cifrada: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "("
            "id_priv_usuario IS NOT NULL AND id_priv_admin IS NULL"
            ") OR ("
            "id_priv_usuario IS NULL AND id_priv_admin IS NOT NULL"
            ")",
            name="chk_contrasenas_propietario"
        ),
    )
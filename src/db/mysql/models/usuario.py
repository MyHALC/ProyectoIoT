from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=False
    )

    id_pub: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        unique=True,
        nullable=False
    )

    usuario: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    activo: Mapped[int] = mapped_column(
        TINYINT(1),
        nullable=False,
        server_default=text("0")
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
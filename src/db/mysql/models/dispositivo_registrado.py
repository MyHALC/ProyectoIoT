from datetime import datetime

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.mysql import INTEGER, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class DispositivoRegistrado(Base):
    __tablename__ = "dispositivos_registrados"

    id_priv_admin: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "administradores.id_priv",
            ondelete="CASCADE"
        ),
        primary_key=True,
        autoincrement=False
    )

    id_priv_dispositivo: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "dispositivos.id_priv",
            ondelete="CASCADE"
        ),
        primary_key=True,
        autoincrement=False
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
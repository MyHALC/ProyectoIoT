from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class DispositivoSeguridad(Base):
    __tablename__ = "dispositivos_seguridad"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "dispositivos.id_priv",
            ondelete="CASCADE"
        ),
        primary_key=True,
        autoincrement=False
    )

    llave_hmac_cifrada: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
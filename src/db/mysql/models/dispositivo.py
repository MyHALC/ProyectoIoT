from sqlalchemy import text
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class Dispositivo(Base):
    __tablename__ = "dispositivos"

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

    activo: Mapped[int] = mapped_column(
        TINYINT(1),
        nullable=False,
        server_default=text("0")
    )
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class DispositivoInfo(Base):
    __tablename__ = "dispositivos_info"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "dispositivos.id_priv",
            ondelete="CASCADE"
        ),
        primary_key=True,
        autoincrement=False
    )

    nombre: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    tipo_disp: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
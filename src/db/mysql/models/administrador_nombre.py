from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class AdministradorNombre(Base):
    __tablename__ = "administradores_nombres"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "administradores.id_priv",
            name="fk_adm_nombres_admin",
            ondelete="CASCADE"
        ),
        primary_key=True,
        autoincrement=False
    )

    nombre: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    apellido: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
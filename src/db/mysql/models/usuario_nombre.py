from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from db.mysql.base import Base


class UsuarioNombre(Base):
    __tablename__ = "usuarios_nombres"

    id_priv: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "usuarios.id_priv",
            ondelete="CASCADE",
            name="fk_usu_nombres_usuarios"
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
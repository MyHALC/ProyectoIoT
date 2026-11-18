from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)



class CorreoBase(BaseModel):

    correo: str = Field(
        ...,
        min_length=5,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    @field_validator("correo", mode="before")
    @classmethod
    def normalizar_correo(cls, valor):
        if isinstance(valor, str):
            return valor.strip().lower()
        return valor



class RegistroRequest(CorreoBase):

    model_config = ConfigDict(extra="forbid")

    usuario: str = Field(
        ..., min_length=3, max_length=30
    )

    nombre: str = Field(
        ..., min_length=1, max_length=30
    )

    apellido: str = Field(
        ..., min_length=1, max_length=50
    )

    contrasena: str = Field(
        ..., min_length=8, max_length=128
    )

    @field_validator(
        "usuario", "nombre", "apellido"
    )
    @classmethod
    def limpiar_texto(cls, valor: str):
        valor = valor.strip()

        if not valor:
            raise ValueError("El campo no puede estar vacío")

        return valor


class LoginRequest(CorreoBase):

    contrasena: str = Field(
        ..., min_length=1
    )


class UsuarioConsultaCorreo(CorreoBase):
    pass


class UsuarioListado(BaseModel):

    limite: int = Field(
        default=50,
        ge=1,
        le=100
    )

class UsuarioResponse(BaseModel):

    id_pub: int
    usuario: str
    nombre: str
    apellido: str
    correo: str
    activo: bool
    fecha_registro: datetime



class LoginRespuesta(BaseModel):

    mensaje: str
    CorreoElectronico: str
    usuario: UsuarioResponse
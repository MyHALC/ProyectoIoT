import base64
import re
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)


PATRON_ID_SES_APP = r"^[0-9a-f]{32}$"
PATRON_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _decodificar_b64url(valor: str) -> bytes:
    return base64.urlsafe_b64decode(valor + "=" * (-len(valor) % 4))


class VerificacionFrontendRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    Id_c: str | int = Field(
        ...,
        description="Identificador del cliente: correo o id_pub numérico"
    )

    PL_c: str = Field(
        ...,
        min_length=10,
        max_length=8192,
        description="Mensaje cifrado con AES-256-GCM en formato s1.<iv>.<ct>"
    )

    sal: str = Field(
        ...,
        min_length=8,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Sal / nonce de un solo uso (anti-replay)"
    )

    codigo: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="HMAC-SHA256 en hexadecimal calculado con Llave_ses_app"
    )

    ID_ses_app: str | None = Field(
        default=None,
        description="ID de la sesión de aplicación (también puede llegar en X-App-Session-Id)"
    )

    tipo_app_esperado: Literal["users", "admin"] | None = Field(
        default=None,
        description="Rol que debe tener la aplicación emisora (opcional)"
    )

    @field_validator("Id_c")
    @classmethod
    def validar_id_c(cls, valor):
        texto = str(valor).strip().lower()

        if texto.isdigit():
            numero = int(texto)
            if not 1 <= numero <= 4294967295:
                raise ValueError("El id_pub debe estar entre 1 y 4294967295")
            return texto

        if not re.match(PATRON_CORREO, texto) or len(texto) > 254:
            raise ValueError("Id_c debe ser un correo válido o un id_pub numérico")

        return texto

    @field_validator("PL_c")
    @classmethod
    def validar_estructura_mensaje(cls, valor: str):
        valor = valor.strip()
        partes = valor.split(".")

        if len(partes) != 3 or partes[0] != "s1":
            raise ValueError("PL_c debe tener el formato s1.<iv>.<ct>")

        try:
            nonce = _decodificar_b64url(partes[1])
            texto_cifrado = _decodificar_b64url(partes[2])
        except Exception:
            raise ValueError("PL_c contiene Base64 URL-safe inválido")

        if len(nonce) != 12:
            raise ValueError("El IV de PL_c debe medir 12 bytes")

        if len(texto_cifrado) < 17:
            raise ValueError("PL_c no contiene texto cifrado + etiqueta GCM de 16 bytes")

        return valor

    @field_validator("codigo")
    @classmethod
    def validar_codigo_hex(cls, valor: str):
        valor = valor.strip().lower()

        if not re.match(r"^[0-9a-f]{64}$", valor):
            raise ValueError("codigo debe ser HMAC-SHA256 en hexadecimal (64 caracteres)")

        return valor

    @field_validator("ID_ses_app")
    @classmethod
    def validar_id_ses_app(cls, valor):
        if valor is None:
            return None

        valor = valor.strip().lower()

        if not re.match(PATRON_ID_SES_APP, valor):
            raise ValueError("ID_ses_app debe ser hexadecimal de 32 caracteres")

        return valor


class SesionAppPublica(BaseModel):

    APP: int
    tipo_app: str
    nombre_app: str
    origen_cors: str
    segundos_restantes: int


class VerificacionFrontendResponse(BaseModel):

    mensaje: str
    valido: bool
    Id_c: str
    sesion_app: SesionAppPublica

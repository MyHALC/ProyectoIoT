from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    AwareDatetime,
    field_validator
)


# ===============================
# REGISTRAR DATOS IOT
# ===============================

class RegistroIoTEntrada(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    id_priv_dispositivo: int = Field(
        ...,
        gt=0
    )

    fecha_generacion: AwareDatetime

    payload: dict[str, Any] = Field(
        ...,
        min_length=1
    )

    @field_validator("fecha_generacion")
    @classmethod
    def normalizar_fecha(cls, valor: datetime):
        return valor.astimezone(timezone.utc)


# ===============================
# CONSULTAR POR DISPOSITIVO
# ===============================

class RegistroIoTConsulta(BaseModel):

    id_priv_dispositivo: int = Field(
        ...,
        gt=0
    )


# ===============================
# RESPUESTA DE REGISTRO
# ===============================

class RegistroIoTResponse(BaseModel):

    id: str

    id_priv_dispositivo: int

    fecha_generacion: datetime

    fecha_recepcion: datetime

    payload: dict[str, Any]


# ===============================
# VERIFICAR CONEXIÓN
# ===============================

class MongoConexionResponse(BaseModel):

    estado: str
    base_datos: str
    coleccion: str
    tipo: str
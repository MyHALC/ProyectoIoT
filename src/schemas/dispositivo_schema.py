from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)


# ============================
# REGISTRAR DISPOSITIVO
# ============================

class DispositivoRegistroRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    id_pub_administrador: int = Field(
        ...,
        ge=1,
        le=4294967295
    )

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=30
    )

    tipo_disp: str = Field(
        ...,
        min_length=1,
        max_length=30
    )

    @field_validator("nombre", "tipo_disp")
    @classmethod
    def limpiar_texto(cls, valor: str):

        valor = valor.strip()

        if not valor:
            raise ValueError(
                "El campo no puede estar vacío"
            )

        return valor


# ============================
# CONSULTAR POR ID PÚBLICO
# ============================

class DispositivoConsultaID(BaseModel):

    id_pub: int = Field(
        ...,
        ge=1,
        le=4294967295
    )


# ============================
# CONSULTAR POR ADMINISTRADOR
# ============================

class DispositivoConsultaAdministrador(BaseModel):

    id_pub_administrador: int = Field(
        ...,
        ge=1,
        le=4294967295
    )


# ============================
# LISTADO
# ============================

class DispositivoListado(BaseModel):

    limite: int = Field(
        default=50,
        ge=1,
        le=100
    )


# ============================
# RESPUESTA DE DISPOSITIVO
# ============================

class DispositivoResponse(BaseModel):

    id_pub: int
    nombre: str
    tipo_disp: str
    activo: bool


# ============================
# RESPUESTA DE REGISTRO
# ============================

class DispositivoRegistroResponse(DispositivoResponse):

    id_pub_administrador: int
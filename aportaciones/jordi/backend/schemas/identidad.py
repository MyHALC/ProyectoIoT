from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class RegistroPersona(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=1, max_length=30)
    apellido: str = Field(min_length=1, max_length=50)
    usuario: str | None = Field(default=None, min_length=1, max_length=30)
    correo: str = Field(min_length=5, max_length=254, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    contrasena: str = Field(min_length=4, max_length=128,
                            validation_alias=AliasChoices('contrasena', 'contraseña'))

    @field_validator('nombre', 'apellido', 'usuario', 'correo', mode='before')
    @classmethod
    def limpiar_datos_personales(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor


class RegistroDispositivo(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    nombre: str = Field(min_length=1, max_length=30)
    tipo_disp: str = Field(min_length=1, max_length=30)

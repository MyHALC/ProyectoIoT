import base64
from pydantic import (BaseModel,ConfigDict,Field,field_validator)

# ============================
# PAQUETE CIFRADO COMPARTIDO
# ============================

class PaqueteCifrado(BaseModel):    
    model_config = ConfigDict(extra="forbid")       # No permitir campos extra en el modelo es decir, solo se aceptan los campos definidos en la clase
    pl_c: bytes = Field(..., min_length=17, max_length=4096) # Texto cifrado en bytes, longitud mínima 17 bytes y máxima 4096 bytes
    iv: bytes = Field(..., min_length=12, max_length=12) # Vector de inicialización (IV) en bytes, longitud fija de 12
    @field_validator("pl_c", "iv", mode="before")   # @indica que el método se usará para validar los campos antes de la validación estándar
    @classmethod                                    #@classmethod indica que el método recibe la clase como primer argumento en lugar de la instancia
    def convertir_base64(cls, valor):               # Convierte el valor de base64 a bytes si es una cadena, de lo contrario lo devuelve tal cual
        if isinstance(valor, str):
            return base64.b64decode(valor, validate=True)
        return valor

# ============================
# PETICIÓN DE LOGIN CIFRADA     
# ============================

class PeticionLoginCifrada(PaqueteCifrado):
    id_cliente: int = Field(..., ge=1)

# ============================
# PETICIÓN GENÉRICA CIFRADA
# ============================

class PeticionCifrada(PaqueteCifrado):

    id_sesion: str = Field(..., min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]+$")

# ============================
# RESPUESTA CIFRADA
# ============================

class RespuestaCifrada(BaseModel):
    pl_c: str
    iv: str
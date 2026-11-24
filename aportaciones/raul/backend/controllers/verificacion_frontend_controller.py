import re

from fastapi import HTTPException
from redis.exceptions import RedisError

from db.redis.session_repository import (
    obtener_sesion_aplicacion,
    registrar_nonce_sal,
)
from seguridad.criptografia import (
    verificar_codigo_hmac_app,
)
from schemas.verificacion_frontend_schema import (
    PATRON_ID_SES_APP,
    SesionAppPublica,
    VerificacionFrontendRequest,
    VerificacionFrontendResponse,
)


CONTEXTO_NONCE = "verif_frontend"


class VerificacionFrontendController:

    def _resolver_id_ses_app(
        self,
        id_header: str | None,
        id_body: str | None
    ) -> str:
        id_header = (id_header or "").strip().lower() or None

        if id_header and id_body and id_header != id_body:
            raise HTTPException(
                status_code=401,
                detail="1.- Verifica sesión app falló: X-App-Session-Id no coincide con ID_ses_app del paquete"
            )

        id_ses_app = id_header or id_body

        if not id_ses_app:
            raise HTTPException(
                status_code=401,
                detail="1.- Verifica sesión app falló: Falta ID_ses_app (cabecera X-App-Session-Id o campo del paquete)"
            )

        if not re.match(PATRON_ID_SES_APP, id_ses_app):
            raise HTTPException(
                status_code=401,
                detail="1.- Verifica sesión app falló: Formato de ID_ses_app inválido"
            )

        return id_ses_app

    def verificar_paquete_frontend(
        self,
        datos: VerificacionFrontendRequest,
        id_ses_app_header: str | None,
        origen: str | None
    ) -> VerificacionFrontendResponse:

        id_ses_app = self._resolver_id_ses_app(
            id_ses_app_header, datos.ID_ses_app
        )

        # 1.- Verifica datos de la sesión de aplicación en Redis ([ APP | ID_ses_app | Key_app ])
        try:
            sesion_app = obtener_sesion_aplicacion(id_ses_app)
        except RedisError:
            raise HTTPException(
                status_code=503,
                detail="1.- Verifica sesión app falló: Redis no disponible"
            )

        if sesion_app is None:
            raise HTTPException(
                status_code=401,
                detail="1.- Verifica sesión app falló: Sesión de aplicación inexistente o expirada en Redis ([ APP | ID_ses_app | Key_app ])"
            )

        if len(sesion_app["llave_ses_app_bytes"]) != 32:
            raise HTTPException(
                status_code=401,
                detail="1.- Verifica sesión app falló: Key_app no mide 256 bits"
            )

        if datos.tipo_app_esperado and sesion_app["tipo_app"] != datos.tipo_app_esperado:
            raise HTTPException(
                status_code=403,
                detail=f"1.- Verifica sesión app falló: La sesión pertenece al rol '{sesion_app['tipo_app']}', se esperaba '{datos.tipo_app_esperado}'"
            )

        origen_limpio = (origen or "").strip().rstrip("/")
        origen_sesion = (sesion_app["origen_cors"] or "").strip().rstrip("/")

        if origen_limpio and origen_limpio != origen_sesion:
            raise HTTPException(
                status_code=403,
                detail=f"1.- Verifica sesión app (CORS) falló: Origen '{origen_limpio}' no coincide con '{origen_sesion}'"
            )

        # 2.- Verifica código HMAC del mensaje con Key_app de Redis
        if not verificar_codigo_hmac_app(
            sesion_app["llave_ses_app_bytes"],
            datos.Id_c,
            datos.PL_c,
            datos.sal,
            datos.codigo,
        ):
            raise HTTPException(
                status_code=401,
                detail="2.- Verifica código HMAC falló: Código HMAC de aplicación inválido (mensaje alterado o intento de suplantación)"
            )

        # 3.- Verifica anti-replay de la sal del mensaje
        try:
            sal_nueva = registrar_nonce_sal(CONTEXTO_NONCE, datos.sal)
        except RedisError:
            raise HTTPException(
                status_code=503,
                detail="3.- Verifica mensaje (anti-replay) falló: Redis no disponible"
            )

        if not sal_nueva:
            raise HTTPException(
                status_code=401,
                detail="3.- Verifica mensaje (anti-replay) falló: La sal ya fue utilizada (paquete repetido)"
            )

        return VerificacionFrontendResponse(
            mensaje="Paquete del frontend verificado: sesión de aplicación, mensaje y código HMAC válidos",
            valido=True,
            Id_c=str(datos.Id_c),
            sesion_app=SesionAppPublica(
                APP=sesion_app["APP"],
                tipo_app=sesion_app["tipo_app"],
                nombre_app=sesion_app["nombre_app"],
                origen_cors=sesion_app["origen_cors"],
                segundos_restantes=int(sesion_app["segundos_restantes"]),
            ),
        )


verificacion_frontend_controller = VerificacionFrontendController()

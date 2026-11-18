from fastapi import HTTPException
from redis.exceptions import RedisError

from db.redis.session_repository import (
    obtener_sesion,
    eliminar_sesion
)


class SesionesController:

    # ============================
    # CONSULTAR SESIÓN
    # ============================

    def consultar_sesion(
        self,
        session_id: str | None
    ) -> dict:

        if not session_id:
            raise HTTPException(
                status_code=401,
                detail="No existe una sesión activa"
            )

        try:
            datos = obtener_sesion(session_id)

        except RedisError as error:
            raise HTTPException(
                status_code=503,
                detail="Redis no está disponible"
            ) from error

        if datos is None:
            raise HTTPException(
                status_code=401,
                detail="Sesión inválida o expirada"
            )

        return datos

    # ============================
    # CERRAR SESIÓN
    # ============================

    def cerrar_sesion(
        self,
        session_id: str | None
    ) -> dict:

        if session_id:

            try:
                eliminar_sesion(session_id)

            except RedisError as error:
                raise HTTPException(
                    status_code=503,
                    detail="No se pudo eliminar la sesión"
                ) from error

        return {
            "mensaje": "Sesión cerrada correctamente"
        }


sesiones_controller = SesionesController()
import os
import secrets

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError
)
from sqlalchemy.orm import Session

from db.mysql.models import (
    Administrador,
    Dispositivo,
    DispositivoInfo,
    DispositivoSeguridad,
    DispositivoRegistrado
)

from schemas.dispositivo_schema import (
    DispositivoRegistroRequest,
    DispositivoConsultaID,
    DispositivoConsultaAdministrador,
    DispositivoListado,
    DispositivoResponse,
    DispositivoRegistroResponse
)


class DispositivosController:

    # ============================
    # GENERAR IDENTIFICADORES
    # ============================

    def generar_id(self) -> int:

        return secrets.randbelow(2**32 - 1) + 1

    # ============================
    # CONSULTA BASE ORM
    # ============================

    def consulta_dispositivos(self):

        return (
            select(
                Dispositivo.id_pub,
                Dispositivo.activo,
                DispositivoInfo.nombre,
                DispositivoInfo.tipo_disp
            )
            .select_from(Dispositivo)
            .join(
                DispositivoInfo,
                DispositivoInfo.id_priv
                == Dispositivo.id_priv
            )
        )

    # ============================
    # REGISTRAR DISPOSITIVO
    # ============================

    def registrar_dispositivo(
        self,
        datos: DispositivoRegistroRequest,
        db: Session
    ) -> DispositivoRegistroResponse:

        # Habilitación solamente para
        # pruebas locales.
        habilitado = os.getenv(
            "DISPOSITIVOS_DEMO_REGISTRO_HABILITADO",
            "false"
        ).strip().lower() == "true"

        if not habilitado:
            raise HTTPException(
                status_code=403,
                detail="Registro de dispositivos deshabilitado"
            )

        # Buscar administrador mediante ID público
        administrador = db.scalar(
            select(Administrador).where(
                Administrador.id_pub
                == datos.id_pub_administrador
            )
        )

        if administrador is None:
            raise HTTPException(
                status_code=404,
                detail="El administrador no existe"
            )

        if not bool(administrador.activo):
            raise HTTPException(
                status_code=409,
                detail="El administrador está inactivo"
            )

        # IDs provisionales para la demostración
        for _ in range(5):

            id_priv = self.generar_id()
            id_pub = self.generar_id()

            try:
                # 1. Crear identidad
                dispositivo = Dispositivo(
                    id_priv=id_priv,
                    id_pub=id_pub,
                    activo=0
                )

                db.add(dispositivo)
                db.flush()

                # 2. Crear información
                informacion = DispositivoInfo(
                    id_priv=id_priv,
                    nombre=datos.nombre,
                    tipo_disp=datos.tipo_disp
                )

                # 3. Crear seguridad sin llave HMAC
                seguridad = DispositivoSeguridad(
                    id_priv=id_priv,
                    llave_hmac_cifrada=None
                )

                # 4. Asociar con administrador
                registro = DispositivoRegistrado(
                    id_priv_admin=administrador.id_priv,
                    id_priv_dispositivo=id_priv
                )

                db.add_all([
                    informacion,
                    seguridad,
                    registro
                ])

                # Guardar las cuatro tablas
                # en una sola transacción.
                db.commit()

                return DispositivoRegistroResponse(
                    id_pub=id_pub,
                    nombre=datos.nombre,
                    tipo_disp=datos.tipo_disp,
                    activo=False,
                    id_pub_administrador=datos.id_pub_administrador
                )

            except IntegrityError as error:

                db.rollback()

                # Comprobar posibles colisiones
                # de identificadores.
                id_priv_ocupado = (
                    db.get(Dispositivo, id_priv)
                    is not None
                )

                id_pub_ocupado = db.scalar(
                    select(Dispositivo.id_priv).where(
                        Dispositivo.id_pub == id_pub
                    )
                ) is not None

                if id_priv_ocupado or id_pub_ocupado:
                    continue

                raise HTTPException(
                    status_code=409,
                    detail="Conflicto al registrar el dispositivo"
                ) from error

            except SQLAlchemyError as error:

                db.rollback()

                raise HTTPException(
                    status_code=503,
                    detail="No se pudo guardar el dispositivo"
                ) from error

        raise HTTPException(
            status_code=500,
            detail="No se pudieron asignar IDs únicos"
        )

    # ============================
    # LISTAR DISPOSITIVOS
    # ============================

    def listar_dispositivos(
        self,
        datos: DispositivoListado,
        db: Session
    ) -> list[DispositivoResponse]:

        consulta = (
            self.consulta_dispositivos()
            .order_by(Dispositivo.id_pub)
            .limit(datos.limite)
        )

        filas = db.execute(
            consulta
        ).mappings().all()

        return [
            DispositivoResponse(**dict(fila))
            for fila in filas
        ]

    # ============================
    # CONSULTAR POR ID PÚBLICO
    # ============================

    def obtener_dispositivo_por_id(
        self,
        datos: DispositivoConsultaID,
        db: Session
    ) -> DispositivoResponse:

        consulta = (
            self.consulta_dispositivos()
            .where(
                Dispositivo.id_pub == datos.id_pub
            )
        )

        fila = db.execute(
            consulta
        ).mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Dispositivo no encontrado"
            )

        return DispositivoResponse(
            **dict(fila)
        )

    # ============================
    # DISPOSITIVOS DE ADMINISTRADOR
    # ============================

    def obtener_dispositivos_administrador(
        self,
        datos: DispositivoConsultaAdministrador,
        db: Session
    ) -> list[DispositivoResponse]:

        administrador = db.scalar(
            select(Administrador.id_priv).where(
                Administrador.id_pub
                == datos.id_pub_administrador
            )
        )

        if administrador is None:
            raise HTTPException(
                status_code=404,
                detail="El administrador no existe"
            )

        consulta = (
            self.consulta_dispositivos()
            .join(
                DispositivoRegistrado,
                DispositivoRegistrado.id_priv_dispositivo
                == Dispositivo.id_priv
            )
            .where(
                DispositivoRegistrado.id_priv_admin
                == administrador
            )
            .order_by(Dispositivo.id_pub)
        )

        filas = db.execute(
            consulta
        ).mappings().all()

        return [
            DispositivoResponse(**dict(fila))
            for fila in filas
        ]


dispositivos_controller = DispositivosController()
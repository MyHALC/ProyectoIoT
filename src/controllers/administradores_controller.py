import os
import secrets

from fastapi import HTTPException
from pwdlib import PasswordHash

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.mysql.models import (
    Administrador,
    AdministradorNombre,
    Correo,
    Contrasena
)

from schemas.administrador_schema import (
    AdministradorRegistroRequest,
    AdministradorLoginRequest,
    AdministradorConsultaCorreo,
    AdministradorListado,
    AdministradorResponse,
    AdministradorLoginResponse
)

from redis.exceptions import RedisError

from db.redis.session_repository import crear_sesion


password_hash = PasswordHash.recommended()


class AdministradoresController:

    # ============================
    # GENERAR IDENTIFICADORES
    # ============================

    def generar_id(self) -> int:
        return secrets.randbelow(4294967295) + 1

    # ============================
    # CONSULTA BASE ORM
    # ============================

    def consulta_administradores(self):

        return (
            select(
                Administrador.id_pub,
                Administrador.usuario,
                Administrador.activo,
                Administrador.es_master,
                Administrador.fecha_registro,
                AdministradorNombre.nombre,
                AdministradorNombre.apellido,
                Correo.correo
            )
            .select_from(Administrador)
            .join(
                AdministradorNombre,
                AdministradorNombre.id_priv
                == Administrador.id_priv
            )
            .join(
                Correo,
                Correo.id_priv_admin
                == Administrador.id_priv
            )
        )

    # ============================
    # REGISTRAR ADMINISTRADOR
    # ============================

    # ============================
    # REGISTRAR ADMINISTRADOR
    # ============================

    def crear_administrador(
            self,
            datos: AdministradorRegistroRequest,
            db: Session
    ) -> AdministradorResponse:

        habilitado = os.getenv(
            "ADMIN_DEMO_REGISTRO_HABILITADO",
            "false"
        ).strip().lower() == "true"

        if not habilitado:
            raise HTTPException(
                status_code=403,
                detail="Registro de administradores deshabilitado"
            )

        # Generar hash Argon2id
        hash_guardado = password_hash.hash(
            datos.contrasena
        )

        # Bloqueo exclusivo para serializar
        # los registros de administradores.
        nombre_bloqueo = "iot2:registro_administradores"

        # El bloqueo utiliza una conexión separada
        # para conservarlo durante db.commit().
        with db.get_bind().connect() as conexion_bloqueo:

            try:
                bloqueo = conexion_bloqueo.scalar(
                    text("SELECT GET_LOCK(:nombre, 10)"),
                    {"nombre": nombre_bloqueo}
                )

            except SQLAlchemyError as error:
                raise HTTPException(
                    status_code=503,
                    detail="No se pudo obtener el bloqueo de registro"
                ) from error

            if bloqueo != 1:
                raise HTTPException(
                    status_code=503,
                    detail="El registro está ocupado. Intenta nuevamente."
                )

            try:
                # ============================
                # VALIDAR CORREO
                # ============================

                existe_correo = db.scalar(
                    select(Correo.id_priv).where(
                        Correo.correo == datos.correo
                    )
                )

                if existe_correo is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="El correo ya está registrado"
                    )

                # ============================
                # VALIDAR NOMBRE DE USUARIO
                # ============================

                existe_usuario = db.scalar(
                    select(Administrador.id_priv).where(
                        Administrador.usuario == datos.usuario
                    )
                )

                if existe_usuario is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="El nombre de usuario ya está registrado"
                    )

                # ============================
                # DETERMINAR ADMINISTRADOR MASTER
                # ============================

                existe_admin = db.scalar(
                    select(Administrador.id_priv).limit(1)
                )

                # Si no hay administradores: master.
                # Si ya existe alguno: normal.
                es_master = 1 if existe_admin is None else 0

                # ============================
                # REGISTRAR ADMINISTRADOR
                # ============================

                for _ in range(5):

                    id_priv = self.generar_id()
                    id_pub = self.generar_id()

                    try:
                        administrador = Administrador(
                            id_priv=id_priv,
                            id_pub=id_pub,
                            usuario=datos.usuario,
                            activo=1,
                            es_master=es_master
                        )

                        db.add(administrador)
                        db.flush()

                        db.add_all([
                            AdministradorNombre(
                                id_priv=id_priv,
                                nombre=datos.nombre,
                                apellido=datos.apellido
                            ),

                            Correo(
                                id_priv_usuario=None,
                                id_priv_admin=id_priv,
                                correo=datos.correo
                            ),

                            Contrasena(
                                id_priv_usuario=None,
                                id_priv_admin=id_priv,
                                contrasena=hash_guardado,
                                contra_cambiada=0,
                                llave_hmac_cifrada=None
                            )
                        ])

                        # Guardar todas las tablas
                        # en una sola transacción.
                        db.commit()
                        db.refresh(administrador)

                        return AdministradorResponse(
                            id_pub=administrador.id_pub,
                            usuario=administrador.usuario,
                            nombre=datos.nombre,
                            apellido=datos.apellido,
                            correo=datos.correo,
                            activo=bool(administrador.activo),
                            es_master=bool(administrador.es_master),
                            fecha_registro=administrador.fecha_registro
                        )

                    except IntegrityError as error:

                        db.rollback()

                        # Comprobar correo duplicado
                        correo_ocupado = db.scalar(
                            select(Correo.id_priv).where(
                                Correo.correo == datos.correo
                            )
                        )

                        if correo_ocupado is not None:
                            raise HTTPException(
                                status_code=409,
                                detail="El correo ya está registrado"
                            ) from error

                        # Comprobar colisiones de ID
                        id_priv_ocupado = (
                                db.get(Administrador, id_priv)
                                is not None
                        )

                        id_pub_ocupado = db.scalar(
                            select(Administrador.id_priv).where(
                                Administrador.id_pub == id_pub
                            )
                        ) is not None

                        if id_priv_ocupado or id_pub_ocupado:
                            continue

                        raise HTTPException(
                            status_code=409,
                            detail="Conflicto al registrar el administrador"
                        ) from error

                raise HTTPException(
                    status_code=500,
                    detail="No se pudieron asignar identificadores únicos"
                )

            except SQLAlchemyError as error:

                db.rollback()

                raise HTTPException(
                    status_code=503,
                    detail="No se pudo guardar el administrador"
                ) from error

            finally:
                # Liberar el bloqueo, tanto si
                # el registro fue exitoso como si falló.
                try:
                    conexion_bloqueo.scalar(
                        text("SELECT RELEASE_LOCK(:nombre)"),
                        {"nombre": nombre_bloqueo}
                    )

                except SQLAlchemyError:
                    # Evitar reutilizar una conexión que
                    # pudiera conservar el bloqueo.
                    conexion_bloqueo.invalidate()


    def validar_administrador(
            self,
            datos: AdministradorLoginRequest,
            db: Session
    ) -> tuple[AdministradorLoginResponse, str]:

        consulta = (
            self.consulta_administradores()
            .add_columns(
                Contrasena.contrasena.label(
                    "hash_guardado"
                )
            )
            .join(
                Contrasena,
                Contrasena.id_priv_admin
                == Administrador.id_priv
            )
            .where(
                Correo.correo == datos.correo
            )
        )

        fila = db.execute(
            consulta
        ).mappings().first()

        error_login = HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

        if fila is None:
            raise error_login

        if not bool(fila["activo"]):
            raise error_login

        hash_almacenado = fila["hash_guardado"]

        if not hash_almacenado.startswith("$argon2id$"):
            raise error_login

        if not password_hash.verify(
                datos.contrasena,
                hash_almacenado
        ):
            raise error_login

        administrador = AdministradorResponse(
            id_pub=fila["id_pub"],
            usuario=fila["usuario"],
            nombre=fila["nombre"],
            apellido=fila["apellido"],
            correo=fila["correo"],
            activo=bool(fila["activo"]),
            es_master=bool(fila["es_master"]),
            fecha_registro=fila["fecha_registro"]
        )

        resultado = AdministradorLoginResponse(
            mensaje="Inicio de sesión correcto",
            CorreoElectronico=administrador.correo,
            administrador=administrador
        )

        # ============================
        # CREAR SESIÓN REDIS
        # ============================

        try:
            session_id = crear_sesion(
                tipo_cuenta="administrador",
                id_pub=administrador.id_pub
            )

        except RedisError as error:
            raise HTTPException(
                status_code=503,
                detail="No se pudo crear la sesión en Redis"
            ) from error

        return resultado, session_id

    # ============================
    # LISTAR ADMINISTRADORES
    # ============================

    def listar_administradores(
        self,
        datos: AdministradorListado,
        db: Session
    ) -> list[AdministradorResponse]:

        consulta = (
            self.consulta_administradores()
            .order_by(Administrador.id_pub)
            .limit(datos.limite)
        )

        filas = db.execute(
            consulta
        ).mappings().all()

        return [
            AdministradorResponse(**dict(fila))
            for fila in filas
        ]

    # ============================
    # CONSULTAR POR CORREO
    # ============================

    def obtener_administrador_por_correo(
        self,
        datos: AdministradorConsultaCorreo,
        db: Session
    ) -> AdministradorResponse:

        consulta = (
            self.consulta_administradores()
            .where(
                Correo.correo == datos.correo
            )
        )

        fila = db.execute(
            consulta
        ).mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Administrador no encontrado"
            )

        return AdministradorResponse(**dict(fila))


administradores_controller = AdministradoresController()
import os
import secrets

from fastapi import HTTPException
from pwdlib import PasswordHash

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.mysql.models import (
    Usuario,
    UsuarioNombre,
    Correo,
    Contrasena
)

from schemas.usuario_schema import (
    RegistroRequest,
    LoginRequest,
    UsuarioConsultaCorreo,
    UsuarioListado,
    UsuarioResponse,
    LoginRespuesta
)

from redis.exceptions import RedisError

from db.redis.session_repository import crear_sesion

password_hash = PasswordHash.recommended()


class UsuariosController:

    # ============================
    # GENERAR IDENTIFICADORES
    # ============================

    def generar_id(self) -> int:
        return secrets.randbelow(4294967295) + 1

    # ============================
    # CONSULTA BASE ORM
    # ============================

    def consulta_usuarios(self):

        return (
            select(
                Usuario.id_pub,
                Usuario.usuario,
                Usuario.activo,
                Usuario.fecha_registro,
                UsuarioNombre.nombre,
                UsuarioNombre.apellido,
                Correo.correo
            )
            .select_from(Usuario)
            .join(
                UsuarioNombre,
                UsuarioNombre.id_priv == Usuario.id_priv
            )
            .join(
                Correo,
                Correo.id_priv_usuario == Usuario.id_priv
            )
        )

    # ============================
    # REGISTRAR USUARIO
    # ============================

    def crear_usuario(
        self,
        datos: RegistroRequest,
        db: Session
    ) -> UsuarioResponse:

        # Buscar correo en la tabla compartida.
        # Esto verifica usuarios Y administradores.
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

        hash_guardado = password_hash.hash(
            datos.contrasena
        )

        activar_demo = os.getenv(
            "USUARIOS_DEMO_ACTIVAR",
            "false"
        ).lower() == "true"

        # Las tablas principales conservan
        # identificadores asignados por Python.
        for _ in range(5):

            id_priv = self.generar_id()
            id_pub = self.generar_id()

            try:
                # Tabla usuarios
                usuario = Usuario(
                    id_priv=id_priv,
                    id_pub=id_pub,
                    usuario=datos.usuario,
                    activo=int(activar_demo)
                )

                db.add(usuario)
                db.flush()

                # Tablas relacionadas
                db.add_all([
                    UsuarioNombre(
                        id_priv=id_priv,
                        nombre=datos.nombre,
                        apellido=datos.apellido
                    ),

                    Correo(
                        id_priv_usuario=id_priv,
                        id_priv_admin=None,
                        correo=datos.correo
                    ),

                    Contrasena(
                        id_priv_usuario=id_priv,
                        id_priv_admin=None,
                        contrasena=hash_guardado,
                        contra_cambiada=0,
                        llave_hmac_cifrada=None
                    )
                ])

                # Una sola transacción
                db.commit()
                db.refresh(usuario)

                return UsuarioResponse(
                    id_pub=usuario.id_pub,
                    usuario=usuario.usuario,
                    nombre=datos.nombre,
                    apellido=datos.apellido,
                    correo=datos.correo,
                    activo=bool(usuario.activo),
                    fecha_registro=usuario.fecha_registro
                )

            except IntegrityError as error:

                db.rollback()

                # El correo podría haberse registrado
                # desde otra solicitud concurrente.
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

                # Comprobar colisiones de IDs.
                id_priv_ocupado = (
                    db.get(Usuario, id_priv) is not None
                )

                id_pub_ocupado = db.scalar(
                    select(Usuario.id_priv).where(
                        Usuario.id_pub == id_pub
                    )
                ) is not None

                if id_priv_ocupado or id_pub_ocupado:
                    continue

                raise HTTPException(
                    status_code=409,
                    detail="Conflicto al registrar el usuario"
                ) from error

            except SQLAlchemyError as error:

                db.rollback()

                raise HTTPException(
                    status_code=503,
                    detail="No se pudo guardar el usuario"
                ) from error

        raise HTTPException(
            status_code=500,
            detail="No se pudieron asignar identificadores únicos"
        )

    # ============================
    # LOGIN DE USUARIO
    # ============================
    def validar_usuario(
            self,
            datos: LoginRequest,
            db: Session
    ) -> tuple[LoginRespuesta, str]:

        consulta = (
            self.consulta_usuarios()
            .add_columns(
                Contrasena.contrasena.label(
                    "hash_guardado"
                )
            )
            .join(
                Contrasena,
                Contrasena.id_priv_usuario == Usuario.id_priv
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

        usuario = UsuarioResponse(
            id_pub=fila["id_pub"],
            usuario=fila["usuario"],
            nombre=fila["nombre"],
            apellido=fila["apellido"],
            correo=fila["correo"],
            activo=bool(fila["activo"]),
            fecha_registro=fila["fecha_registro"]
        )

        resultado = LoginRespuesta(
            mensaje="Inicio de sesión correcto",
            CorreoElectronico=usuario.correo,
            usuario=usuario
        )

        # ============================
        # CREAR SESIÓN EN REDIS
        # ============================

        try:
            session_id = crear_sesion(
                tipo_cuenta="usuario",
                id_pub=usuario.id_pub
            )

        except RedisError as error:
            raise HTTPException(
                status_code=503,
                detail="No se pudo crear la sesión Redis"
            ) from error

        return resultado, session_id
    # ============================
    # LISTAR USUARIOS
    # ============================

    def listar_usuarios(
        self,
        datos: UsuarioListado,
        db: Session
    ) -> list[UsuarioResponse]:

        consulta = (
            self.consulta_usuarios()
            .order_by(Usuario.id_pub)
            .limit(datos.limite)
        )

        filas = db.execute(
            consulta
        ).mappings().all()

        return [
            UsuarioResponse(**dict(fila))
            for fila in filas
        ]

    # ============================
    # CONSULTAR POR CORREO
    # ============================

    def obtener_usuario_por_correo(
        self,
        datos: UsuarioConsultaCorreo,
        db: Session
    ) -> UsuarioResponse:

        consulta = (
            self.consulta_usuarios()
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
                detail="Usuario no encontrado"
            )

        return UsuarioResponse(**dict(fila))


usuarios_controller = UsuariosController()
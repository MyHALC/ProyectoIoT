from dataclasses import dataclass
import secrets
from sqlalchemy import and_, or_, select
from .models import (Usuario, UsuarioNombre, Administrador, AdministradorNombre, Correo,
                     Contrasena, Dispositivo, DispositivoInfo, DispositivoSeguridad,
                     DispositivoRegistrado)


@dataclass(frozen=True)
class Identidad:
    tipo: str
    fila: object
    seguridad: object
    info: object
    correo: str | None = None

    @property
    def id_pub(self):
        return self.fila.id_pub

    @property
    def id_priv(self):
        return self.fila.id_priv

    @property
    def llave(self):
        return self.seguridad.llave_hmac_cifrada

    def alias(self):
        return {str(self.id_pub)} if self.tipo == 'dispositivo' else {self.fila.usuario, self.correo}

    def publica(self):
        datos = {'id_pub': self.id_pub, 'activo': bool(self.fila.activo), 'nombre': self.info.nombre}
        if self.tipo == 'dispositivo':
            return {**datos, 'tipo_disp': self.info.tipo_disp}
        return {**datos, 'usuario': self.fila.usuario, 'apellido': self.info.apellido, 'correo': self.correo,
                'fecha_registro': self.fila.fecha_registro.isoformat() if self.fila.fecha_registro else None}


class RepositorioIdentidades:
    personas = {'usuario': (Usuario, UsuarioNombre), 'administrador': (Administrador, AdministradorNombre)}

    def __init__(self, db):
        self.db = db

    @staticmethod
    def propietario(tabla, tipo, id_priv):
        if tipo == 'usuario':
            return (tabla.id_priv_usuario == id_priv, tabla.id_priv_admin.is_(None))
        return (tabla.id_priv_admin == id_priv, tabla.id_priv_usuario.is_(None))

    def tabla(self, tipo):
        return Dispositivo if tipo == 'dispositivo' else self.personas[tipo][0]

    def componer(self, tipo, fila):
        if fila is None:
            return None
        if tipo == 'dispositivo':
            datos = self.db.get(DispositivoInfo, fila.id_priv)
            seguridad = self.db.get(DispositivoSeguridad, fila.id_priv)
            return Identidad(tipo, fila, seguridad, datos) if datos and seguridad else None
        datos = self.db.get(self.personas[tipo][1], fila.id_priv)
        correo = self.db.scalar(select(Correo).where(*self.propietario(Correo, tipo, fila.id_priv)))
        seguridad = self.db.scalar(select(Contrasena).where(*self.propietario(Contrasena, tipo, fila.id_priv)))
        return Identidad(tipo, fila, seguridad, datos, correo.correo) if datos and correo and seguridad else None

    def por_id(self, tipo, id_pub):
        tabla = self.tabla(tipo)
        return self.componer(tipo, self.db.scalar(select(tabla).where(tabla.id_pub == id_pub)))

    def buscar_persona(self, tipo, alias):
        tabla = self.tabla(tipo)
        consulta = select(tabla).join(Correo, and_(*self.propietario(Correo, tipo, tabla.id_priv))).where(
            or_(Correo.correo == alias.strip().lower(), tabla.usuario == alias.strip())).limit(2)
        filas = list(self.db.scalars(consulta))
        return self.componer(tipo, filas[0]) if len(filas) == 1 else None

    def listar(self, tipo):
        tabla = self.tabla(tipo)
        return [e for fila in self.db.scalars(select(tabla).order_by(tabla.id_pub))
                if (e := self.componer(tipo, fila)) is not None]

    def ids(self, tabla):
        for _ in range(10):
            privado, publico = (secrets.randbelow(2**32 - 1) + 1 for _ in range(2))
            if privado != publico and self.db.get(tabla, privado) is None and self.db.scalar(
                    select(tabla.id_priv).where(tabla.id_pub == publico)) is None:
                return privado, publico
        raise RuntimeError('No se pudo asignar una identidad nueva.')

    def crear_persona(self, tipo, datos, hash_guardado):
        tabla, nombres = self.personas[tipo]
        correo = datos.correo.strip().lower()
        if self.db.scalar(select(Correo.id_priv).where(Correo.correo == correo)) is not None:
            raise ValueError('El correo ya está registrado.')
        if self.buscar_persona(tipo, correo):
            raise ValueError('El correo coincide con otro alias.')
        if datos.usuario is not None and self.buscar_persona(tipo, datos.usuario):
            raise ValueError('El usuario ya está registrado.')
        usuario = datos.usuario or self.usuario_automatico(tipo, correo)
        privado, publico = self.ids(tabla)
        fila = tabla(id_priv=privado, id_pub=publico, usuario=usuario, activo=0)
        self.db.add(fila)
        self.db.flush()
        propietario = {'id_priv_usuario': privado, 'id_priv_admin': None} if tipo == 'usuario' else {'id_priv_admin': privado, 'id_priv_usuario': None}
        info = nombres(id_priv=privado, nombre=datos.nombre, apellido=datos.apellido)
        seguridad = Contrasena(**propietario, contrasena=hash_guardado, contra_cambiada=0, llave_hmac_cifrada=None)
        self.db.add_all([info, seguridad, Correo(**propietario, correo=correo)])
        self.db.flush()
        return Identidad(tipo, fila, seguridad, info, correo)

    def usuario_automatico(self, tipo, correo):
        base = correo.split('@', 1)[0][:30]
        usuario = base
        numero = 2
        while self.buscar_persona(tipo, usuario):
            sufijo = f'-{numero}'
            usuario = base[:30 - len(sufijo)] + sufijo
            numero += 1
        return usuario

    def crear_dispositivo(self, datos, admin):
        privado, publico = self.ids(Dispositivo)
        fila = Dispositivo(id_priv=privado, id_pub=publico, activo=0)
        self.db.add(fila)
        self.db.flush()
        info = DispositivoInfo(id_priv=privado, nombre=datos.nombre, tipo_disp=datos.tipo_disp)
        seguridad = DispositivoSeguridad(id_priv=privado, llave_hmac_cifrada=None)
        self.db.add_all([info, seguridad, DispositivoRegistrado(id_priv_admin=admin.id_priv, id_priv_dispositivo=privado)])
        self.db.flush()
        return Identidad('dispositivo', fila, seguridad, info)

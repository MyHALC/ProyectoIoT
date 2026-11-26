"""Crea la primera cuenta (administrador master). Se ejecuta una sola vez, con Docker arriba:

    python crear_master.py
"""
import getpass
import secrets
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

import db  # noqa: E402
import seguridad  # noqa: E402
from api import PATRON_CORREO, PATRON_USUARIO  # noqa: E402

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%"


def pedir(etiqueta):
    return input(f"{etiqueta}: ").strip()


def main():
    try:
        conexion = db.conectar()
    except pymysql.err.OperationalError as error:
        print("No se pudo conectar a MySQL. ¿Está en ejecución `docker compose up -d`?")
        print("Detalle:", error)
        return 1

    with conexion:
        with conexion.cursor() as cur:
            cur.execute("SELECT id FROM cuentas WHERE rol = 'master' LIMIT 1")
            if cur.fetchone():
                print("Ya existe un administrador master. No se creó otra cuenta.")
                return 1

        nombre = pedir("Nombre completo")
        correo = pedir("Correo electrónico").lower()
        usuario = pedir("Nombre de usuario")
        if not nombre or len(nombre) > 100:
            print("El nombre es obligatorio (máximo 100 caracteres).")
            return 1
        if not PATRON_CORREO.match(correo) or len(correo) > 254:
            print("El correo no es válido.")
            return 1
        if not PATRON_USUARIO.match(usuario):
            print("Usuario inválido: 3 a 30 caracteres entre letras, números, punto, guion y guion bajo.")
            return 1

        contrasena = getpass.getpass("Contraseña (Enter para generar una provisional): ")
        generada = not contrasena
        if generada:
            contrasena = "".join(secrets.choice(ALFABETO) for _ in range(16))
        elif not 8 <= len(contrasena) <= 128:
            print("La contraseña debe tener entre 8 y 128 caracteres.")
            return 1
        elif contrasena != getpass.getpass("Repite la contraseña: "):
            print("Las contraseñas no coinciden.")
            return 1

        try:
            with conexion.cursor() as cur:
                cur.execute(
                    "INSERT INTO cuentas (rol, nombre_completo, correo, usuario, "
                    "contrasena_hash, contra_cambiada, estado) "
                    "VALUES ('master', %s, %s, %s, %s, %s, 'activo')",
                    (nombre, correo, usuario, seguridad.hashear(contrasena), 0 if generada else 1))
            conexion.commit()
        except pymysql.err.IntegrityError:
            conexion.rollback()
            print("Ese correo o usuario ya existe.")
            return 1

    print(f"Administrador master '{usuario}' creado y activo.")
    if generada:
        print(f"Contraseña provisional (anótala ahora, no se vuelve a mostrar): {contrasena}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

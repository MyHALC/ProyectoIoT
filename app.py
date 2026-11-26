import os
import secrets
from datetime import timedelta
from functools import wraps
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request

load_dotenv(Path(__file__).with_name(".env"))

import db
from api import api, cuenta_actual

app = Flask(__name__)

if not os.getenv("SECRET_KEY"):
    print("AVISO: define SECRET_KEY en .env; sin ella las sesiones se pierden al reiniciar.")
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    # Tope de cualquier petición (la foto de perfil pesa como máximo 2 MB).
        MAX_CONTENT_LENGTH=3 * 1024 * 1024,
)

app.teardown_appcontext(db.cerrar)
app.register_blueprint(api)

def revisar_esquema():
    """Avisa si la base es anterior al perfil (falta la columna `foto`)."""
    try:
        conexion = db.conectar()
    except pymysql.err.Error:
        return  # sin base de datos; el error claro sale en la primera petición
    try:
        with conexion.cursor() as cur:
            cur.execute("SHOW COLUMNS FROM cuentas LIKE 'foto'")
            if cur.fetchone() is None:
                print("AVISO: falta la columna `foto` en la tabla cuentas. Ejecuta "
                      "bd/migraciones/02_perfil.sql (ver README) o el perfil dará error.")
    except pymysql.err.Error:
        pass
    finally:
        conexion.close()


revisar_esquema()

@app.context_processor
def inyectar_cuenta():
    try:
        cuenta = cuenta_actual()
    except pymysql.err.OperationalError:
        cuenta = None

    return {
        "cuenta_sesion": cuenta
    }


@app.after_request
def evitar_cache(respuesta):
    if request.endpoint != "static":
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


def pagina(*roles):
    """Solo deja ver la página a cuentas activas con alguno de esos roles."""
    def decorador(vista):
        @wraps(vista)
        def interna(*args, **kwargs):
            try:
                cuenta = cuenta_actual()
            except pymysql.err.OperationalError:
                return "La base de datos no está disponible. Revisa que Docker esté en ejecución.", 503
            if cuenta is None or cuenta["rol"] not in roles:
                return redirect("/")
            return vista(*args, **kwargs)
        return interna
    return decorador


@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/master")
@pagina("master")
def panel_maestro():
    return render_template("vistaResumenGeneral/master.html")

@app.route("/master/administradores")
@pagina("master")
def gestion_administradores():
    return render_template("vistaRegistros/registrosAdministradores.html")

@app.route("/master/usuarios")
@pagina("master")
def gestion_usuarios():
    return render_template("vistaRegistros/registrosUsuarios.html")

@app.route("/master/dispositivos")
@pagina("master")
def gestion_dispositivos():
    return render_template("vistaRegistros/registrosDispositivos.html")


@app.route("/admin")
@pagina("administrador", "master")
def panel_administrador():
    return render_template("vistaResumenGeneral/admin.html")

@app.route("/admin/usuarios")
@pagina("administrador", "master")
def administracion_usuarios():
    return render_template("vistaRegistros/registrosUsuarios.html")

@app.route("/admin/dispositivos")
@pagina("administrador", "master")
def administracion_dispositivos():
    return render_template("vistaRegistros/registrosDispositivos.html")

@app.route("/usuario")
@pagina("usuario")
def panel_usuario():
    return render_template("/vistaResumenGeneral/usuario.html")

@app.route("/perfil")
@pagina("master", "administrador", "usuario")
def perfil():
    return render_template("vistaPerfil/perfil.html")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

import os

import pymysql
from flask import g
from pymysql.cursors import DictCursor


def conectar():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3307")),
        user=os.getenv("DB_USER", "iot_front"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "iot_frontend"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=5,
    )


def obtener():
    """Una conexión por petición, reutilizada dentro de ella."""
    if "db" not in g:
        g.db = conectar()
    return g.db


def cerrar(error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()

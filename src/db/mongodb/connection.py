import os
from pathlib import Path

from dotenv import load_dotenv
from mongoengine import connect
from mongoengine.connection import (
    get_connection,
    ConnectionFailure
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

MONGO_ALIAS = "iot"
MONGO_COLECCION = "registros_iot"


def conectar_mongodb():

    try:
        return get_connection(alias=MONGO_ALIAS)

    except ConnectionFailure:
        pass

    return connect(
        db=os.getenv(
            "MONGO_DATABASE",
            "iot"
        ),
        host=os.getenv(
            "MONGO_URI",
            "mongodb://127.0.0.1:27017"
        ),
        alias=MONGO_ALIAS,
        serverSelectionTimeoutMS=3000,
        tz_aware=True
    )
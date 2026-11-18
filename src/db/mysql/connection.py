import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


@lru_cache(maxsize=1)
def obtener_engine():

    motor = os.getenv("DB_MOTOR", "mysql").strip().lower()

    if motor not in ("mysql", "mariadb"):
        raise ValueError(
            "DB_MOTOR debe ser 'mysql' o 'mariadb'"
        )

    url = URL.create(
        drivername=f"{motor}+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "sistema_iot"),
        query={"charset": "utf8mb4"}
    )

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800
    )


@lru_cache(maxsize=1)
def obtener_sessionmaker():

    return sessionmaker(
        bind=obtener_engine(),
        autoflush=False,
        expire_on_commit=False
    )


def obtener_db():

    SessionLocal = obtener_sessionmaker()

    with SessionLocal() as db:
        yield db
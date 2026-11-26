import os
import sys

sys.dont_write_bytecode = True

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.redis.connection import redis_client
from routes.verificacion_frontend_routes import router as verificacion_frontend_routes


app = FastAPI(
    title="Módulo de Verificación Frontend - Código HMAC, Mensaje y Sesión de Aplicación",
    version="1.0"
)

app.state.redis = redis_client

ORIGEN_APP_USERS = os.getenv("ORIGEN_CORS_APP_USERS", "http://127.0.0.1:5000")
ORIGEN_APP_ADMIN = os.getenv("ORIGEN_CORS_APP_ADMIN", "http://127.0.0.1:5001")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ORIGEN_APP_USERS,
        ORIGEN_APP_ADMIN,
    ],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "X-App-Session-Id",
        "X-App-Origin",
    ]
)

app.include_router(
    verificacion_frontend_routes,
    prefix="/api/verificacion-frontend",
    tags=["Verificación Frontend (HMAC + Mensaje + Sesión de Aplicación)"]
)

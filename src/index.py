from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#from db.mysql.connection import engine
#from db.mongodb.connection import mongo_client
from db.redis.connection import redis_client

from routes.usuarios_routes import router as usuarios_routes
from routes.registros_iot_routes import router as registros_iot_routes
from routes.administradores_routes import router as administradores_routes
from routes.dispositivos_routes import router as dispositivos_routes
from routes.sesiones_routes import router as sesiones_routes



app = FastAPI(
    title="Servidor FastAPI",
    version="1.0"
)


# Recursos de bases de datos
#app.state.mysql = engine
#app.state.mongodb = mongo_client
app.state.redis = redis_client


# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5000",
        "http://localhost:5000"
    ],
    allow_credentials=True,
    allow_methods=[
        "GET", "POST", "PUT", "DELETE", "OPTIONS"
    ],
    allow_headers=[
        "Content-Type",
        "X-Telemetry-Key",
        "Authorization"
    ]
)


app.include_router(
    administradores_routes,
    prefix="/api/administradores",
    tags=["Administradores"]
)

app.include_router(
    usuarios_routes,
    prefix="/api/usuarios",
    tags=["Usuarios"]
)

app.include_router(
    registros_iot_routes,
    prefix="/api/registros-iot",
    tags=["Registros IoT"]
)

app.include_router(
    dispositivos_routes,
    prefix="/api/dispositivos",
    tags=["Dispositivos"]
)

app.include_router(
    sesiones_routes,
    prefix="/api/sesiones",
    tags=["Sesiones Redis"]
)
@app.get("/")
def inicio():
    return {
        "mensaje": "Servidor funcionando"
    }
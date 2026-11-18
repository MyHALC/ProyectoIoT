# ProyectoIoT

Framework modular para dispositivos IoT. Este repositorio contiene el servidor API, con persistencia en MySQL/MariaDB y MongoDB, y gestión de sesiones mediante Redis.

## Estructura del servidor

```text
ProyectoIoT/
├── controllers/          # Lógica de negocio y coordinación
├── db/
│   ├── mongodb/          # Conexión y modelo de registros IoT
│   ├── mysql/            # Conexión, modelos y persistencia relacional
│   └── redis/            # Conexión y repositorio de sesiones
├── routes/               # Endpoints HTTP de FastAPI
├── schemas/              # Validación de entrada y salida con Pydantic
├── docs/                 # Documentación técnica
├── .env.example          # Plantilla de variables (sin secretos)
├── .gitignore
├── index.py              # Punto de entrada de la API
└── requirements.txt
```

## Requisitos

- Python 3.10 o superior (el código utiliza anotaciones de tipos modernas).
- MySQL o MariaDB.
- MongoDB.
- Redis.

## Configuración local

1. Clona el repositorio y entra al directorio:

   ```bash
   git clone https://github.com/MyHALC/ProyectoIoT.git
   cd ProyectoIoT
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Linux / macOS
   source .venv/bin/activate
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Crea tu archivo local de variables de entorno:

   ```bash
   cp .env.example .env
   ```

   En Windows PowerShell: `Copy-Item .env.example .env`. Edita los valores para tus servicios locales. **Nunca subas el archivo .env ni credenciales reales.**

5. Prepara las bases de datos y servicios MySQL/MariaDB, MongoDB y Redis con los valores configurados en `.env`.

6. Inicia la API desde la raíz del proyecto:

   ```bash
   uvicorn index:app --reload
   ```

   Documentación interactiva: http://127.0.0.1:8000/docs

## Módulos de la API

| Prefijo | Responsabilidad |
|---|---|
| `/api/usuarios` | Registro, autenticación y consulta de usuarios |
| `/api/administradores` | Registro, autenticación y consulta de administradores |
| `/api/dispositivos` | Registro y consulta de dispositivos |
| `/api/registros-iot` | Recepción y consulta de telemetría IoT |
| `/api/sesiones` | Consulta y cierre de sesiones Redis |

La especificación OpenAPI se genera automáticamente en `/openapi.json`.

## Flujo de colaboración

- Cada colaborador debe trabajar en una rama propia, por ejemplo `feature/nombre-modulo`.
- Realizar commits pequeños y descriptivos.
- Abrir un Pull Request hacia `main`; solicitar revisión antes de integrar cambios.
- No versionar `.env`, entornos virtuales, cachés, logs ni datos locales.
- Mantener actualizado `requirements.txt` cuando se agreguen dependencias.

Convención sugerida para commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:` y `chore:`.

## Seguridad

- Las credenciales y llaves deben mantenerse en variables de entorno.
- Usar HTTPS y configurar `COOKIE_SECURE=true` en despliegues HTTPS.
- Restringir los orígenes CORS a los dominios del frontend en producción.
- No registrar contraseñas, tokens de sesión ni secretos en logs.
- Revisar permisos y validaciones antes de exponer endpoints en producción.

## Estado del proyecto

La estructura y módulos descritos corresponden al servidor FastAPI entregado para integrar en este repositorio. La configuración de infraestructura, migraciones de esquema, pruebas automatizadas y despliegue deben completarse y validarse en el entorno del equipo.

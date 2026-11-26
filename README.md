# Frontend IoT con MySQL en Docker

Los formularios de **Administradores**, **Usuarios** y **Dispositivos** ahora guardan y leen de MySQL.
Flask sirve las páginas y la API (`/api/...`); el navegador nunca habla directo con la base.

## Puesta en marcha

Desde esta carpeta (donde está `app.py`):

```powershell
# 1. Configuración
Copy-Item .env.example .env
#    Edita .env: cambia las dos contraseñas y pon un SECRET_KEY:
#    python -c "import secrets; print(secrets.token_hex(32))"

# 2. Base de datos (la primera vez crea las tablas solo)
docker compose up -d
docker compose ps            # espera a que diga "healthy"

# 3. Entorno de Python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Primera cuenta: el administrador master (una sola vez)
.\.venv\Scripts\python.exe crear_master.py

# 5. Arrancar
.\.venv\Scripts\python.exe app.py        # http://127.0.0.1:5000
```

Entra con el master. Desde su panel registras administradores, usuarios y dispositivos.

## Cómo funciona

| Pantalla | Tabla | Notas |
|---|---|---|
| Administradores / Usuarios | `cuentas` (columna `rol`) | Nacen en estado **pendiente**; solo una cuenta **activa** puede iniciar sesión. |
| Dispositivos | `dispositivos` | Nacen **activos**. |

- Las contraseñas se guardan con **Argon2id**; la provisional se muestra solo al registrar.
- `contra_cambiada = 0` en toda cuenta nueva. El login devuelve `requiere_cambio_contrasena: true` mientras siga en 0.
  **Falta** la pantalla/endpoint de cambio de contraseña (que ponga la columna en 1).
- Permisos: el master gestiona administradores, usuarios y dispositivos; un administrador, usuarios y dispositivos.
- Las páginas `/master/*`, `/admin` y `/usuario` exigen sesión con el rol correcto. Si desactivas una cuenta, pierde el acceso de inmediato.
- Tras 5 intentos fallidos de login en 5 minutos se bloquea temporalmente (en memoria; se reinicia con el servidor).

## Comunicación cifrada con el backend

`utils/cifrado.py`. Front y back comparten `LLAVE_SECRETA` (Fernet) en `.env`.

| | Formato |
|---|---|
| Texto plano | La estructura normal del endpoint en JSON, p. ej. `{"id": 3, "estado": "activo"}` |
| Lo que viaja (petición y respuesta) | `{"datos_cifrados": "<token Fernet>"}` |

```python
from utils.cifrado import empaquetar, desempaquetar
sobre = empaquetar({"id": 3, "estado": "activo"})   # para enviar
datos = desempaquetar(sobre)                         # al recibir (ValueError si no es válido)
```

## Comandos útiles

```powershell
# Ver lo guardado
docker exec -it iot_frontend_mysql mysql -u iot_front -p iot_frontend -e "SELECT id,rol,usuario,correo,estado,contra_cambiada FROM cuentas; SELECT * FROM dispositivos;"

# Detener (conserva los datos)
docker compose down

# Borrar TODO y empezar de cero (vuelve a ejecutar bd/01_esquema.sql)
docker compose down -v
```

## Notas

- El puerto de MySQL en tu equipo es **3307** (no 3306) para no chocar con otra base que ya tengas. Se cambia con `DB_PORT` en `.env`.
- `bd/01_esquema.sql` solo se ejecuta cuando el volumen está vacío. Si cambias el esquema, usa `docker compose down -v`.
- `static/js/login.js` apunta a `/api/usuarios` en este mismo servidor. Para usar otro backend, cambia la constante `API`.
- Las tarjetas de **estadísticas y alertas de `master.html`** siguen siendo datos de demostración.
- Esto es para desarrollo (`debug=True`, HTTP). Para producción haría falta HTTPS y `SESSION_COOKIE_SECURE=True`.

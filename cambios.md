# Cambios de esta versión

Esta versión integra los archivos nuevos (plantillas con base y sidebar, rutas nuevas, CSS y JS), el
envío de correo y el cambio de contraseña del primer acceso.

## 1. Estructura de carpetas

```
FastAPI_Frontend/
├─ api.py  app.py  db.py  seguridad.py  crear_master.py
├─ utils/            (NUEVA)  __init__.py  email.py
├─ static/css/       dashboard.css  style.css
├─ static/js/        api.js  cuentas.js  dispositivos.js  login.js
├─ templates/
│  ├─ index.html                      (el tuyo, con la vista de cambio de contraseña añadida)
│  ├─ componentes/                    base.html  sidebar.html
│  ├─ vistaRegistros/                 registrosAdministradores.html  registrosDispositivos.html  registrosUsuarios.html
│  └─ vistaResumenGeneral/            admin.html  master.html  usuario.html
├─ bd/01_esquema.sql  docker-compose.yml  requirements.txt  .env.example
```

Se eliminaron `templates/admin.html`, `master.html`, `usuario.html`, `administradores.html`,
`usuarios.html` y `dispositivos.html` porque ahora viven en `vistaResumenGeneral/` y `vistaRegistros/`.

## 2. Cómo ponerlo en marcha

Si ya tenías la versión anterior, la base de datos no cambia: no hace falta `docker compose down -v`.

1. Reemplaza la carpeta del proyecto por la de este zip, conservando tu `.env` y tu `.venv`.
2. Abre `.env` y agrega al final (no hay que cambiar nada más):
   ```
   CORREO_REMITENTE=tu_correo@gmail.com
   CORREO_CLAVE_APP=clave_de_16_caracteres
   ```
   La clave se crea en la cuenta de Google: Seguridad, Verificación en 2 pasos, Contraseñas de aplicaciones.
   No uses la contraseña normal de Gmail. **No escribas la clave dentro del código**: en el archivo de
   instrucciones venía una clave a la vista; revócala en Google y crea otra.
3. Arranca igual que antes:
   ```powershell
   docker compose up -d
   .\.venv\Scripts\python.exe app.py
   ```
   No hay paquetes nuevos: `smtplib` ya viene con Python.
4. Si todavía no tienes el master: `.\.venv\Scripts\python.exe crear_master.py`.

## 3. Qué cambió, archivo por archivo

| Archivo | Cambio |
|---|---|
| `app.py` | Rutas nuevas apuntan a las plantillas en subcarpetas. Inyecta `cuenta_sesion` a todas las plantillas (la usa el sidebar). Es el de tu zip. |
| `templates/componentes/base.html` y `sidebar.html` | Esqueleto común con menú lateral según el rol, nombre de la persona y botón de cerrar sesión. |
| `templates/vistaRegistros/*` y `vistaResumenGeneral/*` | Pantallas heredan de `base.html`. Es lo de tu zip. |
| `static/css/*`, `static/js/api.js`, `dispositivos.js` | Los de tu zip, sin cambios de lógica. |
| `static/js/cuentas.js` | Tras registrar, el aviso dice si el correo se envió. Si no, recuerda entregar la contraseña provisional a mano. |
| `static/js/login.js` | Del zip, con dos arreglos: el cambio de contraseña ya no llama a `127.0.0.1:8000` (FastAPI) sino a `/api/cambiar-contrasena` de este Flask, y ya no manda el correo (la sesión identifica a la persona). Se agregó el botón Cancelar. |
| `templates/index.html` | Se conserva el tuyo. Se agregó el bloque `vistaCambio` (formulario con `camNueva` y `camConfirmar`) que `login.js` necesita, y se envolvió el login en `vistaLogin`. |
| `utils/email.py` | Nuevo. Envía el correo por Gmail con SSL (465). Lee remitente y clave de `.env`. Incluye usuario y contraseña provisional. |
| `api.py` | (1) `crear_cuenta` envía el correo después de guardar; si falla, la cuenta se crea igual y la respuesta trae `correo_enviado: false`. (2) Con `contra_cambiada = 0`, el login abre una sesión limitada. (3) Endpoint nuevo `POST /api/cambiar-contrasena`. |
| `.env.example` | Variables `CORREO_REMITENTE` y `CORREO_CLAVE_APP`. |

## 4. Cómo funciona el cambio de contraseña

1. Una cuenta nueva tiene `contra_cambiada = 0`. Al iniciar sesión, el servidor abre una **sesión limitada**:
   no entra a ninguna página ni a ninguna ruta de la API, solo puede cambiar la contraseña.
2. `login.js` ve `requiere_cambio_contrasena: true` y muestra el formulario de cambio.
3. `POST /api/cambiar-contrasena` valida 8 a 128 caracteres y que sea distinta de la provisional, guarda el
   hash Argon2id, pone `contra_cambiada = 1` y cierra la sesión.
4. La persona inicia sesión de nuevo, ya con sesión normal.

Esto sigue el diagrama de "Cambio de contraseña". Por eso no se usó el endpoint con correo del zip: cualquiera que
conociera un correo habría podido cambiar la contraseña de esa cuenta sin estar autenticado.

## 5. Qué se pidió en las instrucciones del correo y qué se hizo

| Instrucción | Resultado |
|---|---|
| 1. `utils/email.py` | Hecho, con la clave en `.env`. |
| 2. `GET /verificar-correo/{correo}` | No se agregó. Ya hay validación en el servidor y ese endpoint, abierto al público, revela qué correos están registrados. |
| 3B. Mensajes de duplicado (409) | Ya existían en `crear_cuenta`: mensajes distintos para correo y usuario. |
| 3C. Enviar correo tras crear | Hecho. |
| 4. `fetch` a `/verificar-correo` en `login.js` | No aplica (ese formulario de registro no existe aquí; el registro se hace en las pantallas de gestión). |

## 6. Pendientes y cosas que notar

- El sidebar enlaza "Monitoreo" y "Alertas" a `/master`, que solo entra el master: a un administrador o usuario lo
  devuelve al login. Y "Configuración" apunta a `/master/configuracion`, que no existe (404).
- Las tarjetas de estadísticas y alertas de `master.html`, `admin.html` y `usuario.html` siguen siendo datos de demostración.
- Aún no está el RoT (`llave_hmac_cifrada`) ni el panel de monitoreo.
- Para producción: HTTPS y `SESSION_COOKIE_SECURE=True`.

## 7. Pruebas realizadas

- API: 70 comprobaciones, entre ellas la sesión limitada, el cambio de contraseña, roles, duplicados y bloqueo de intentos.
- Navegador (Chromium): login, vista de cambio de contraseña (con contraseñas distintas y correctas), acceso a la
  página nueva, registro, activar o desactivar, búsqueda y cierre de sesión. Sin errores de JavaScript.
- No se probó el envío real del correo (necesita tu cuenta de Gmail).

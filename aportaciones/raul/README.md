# Aportación de Raúl: Módulo de Verificación Frontend

Módulo FastAPI dedicado a validar los paquetes provenientes del frontend (`POST /api/verificacion-frontend/verificar`) antes de permitir su procesamiento, entregado en la rama `EquipoRaul` dejando intacta la base común de `src/`.

## Alcance

Verifica tres capas de seguridad por cada petición recibida:

1. **Sesión de aplicación en Redis (`[ APP | ID_ses_app | Key_app ]`):**
   - Valida el `ID_ses_app` (por cabecera `X-App-Session-Id` y/o campo JSON, exigiendo coincidencia si llegan ambos).
   - Comprueba que la sesión exista, siga activa (TTL > 0) y que `Key_app` descifrada mida exactamente 256 bits (32 bytes).
   - Valida el rol de aplicación esperado (`users` / `admin`) y el origen CORS (`Origin` / `X-App-Origin`).
2. **Estructura del mensaje cifrado (`PL_c`) y protección Anti-Replay (`sal`):**
   - Valida en Pydantic (`extra="forbid"`) que `PL_c` cumpla el formato `s1.<iv>.<ct>` en Base64 URL-safe (IV de 12 bytes y texto cifrado + tag GCM >= 17 bytes).
   - Registra la `sal` en Redis por 300 segundos para bloquear paquetes repetidos.
3. **Código de autenticación HMAC (`codigo`):**
   - Recalcula `HMAC-SHA256(Key_app, "Id_c|PL_c|sal")` y compara en tiempo constante con `hmac.compare_digest`.
   - Responde `HTTP 200` únicamente con metadatos públicos (`SesionAppPublica`), sin exponer `Key_app` ni `ID_ses_app`.

## Estructura de esta entrega

```text
aportaciones/raul/
├── README.md
└── backend/
    ├── schemas/
    │   └── verificacion_frontend_schema.py       # Archivo nuevo del módulo
    ├── controllers/
    │   └── verificacion_frontend_controller.py   # Archivo nuevo del módulo
    ├── routes/
    │   └── verificacion_frontend_routes.py       # Archivo nuevo del módulo
    ├── db/redis/
    │   ├── connection.py                         # Soporte de conexión Redis
    │   └── session_repository.py                 # Soporte de sesiones de app y anti-replay
    ├── seguridad/
    │   └── criptografia.py                       # Soporte AES-256-GCM y HMAC-SHA256
    ├── index.py                                  # Punto de entrada FastAPI aislado
    ├── requirements.txt                          # Dependencias del módulo
    └── .env.example                              # Plantilla de variables (sin secretos)
```

## Ejecución local aislada

Desde `aportaciones/raul/backend/`:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn index:app --reload
```

Documentación interactiva: `http://127.0.0.1:8000/docs`

No se incluyen secretos reales, archivos `.env`, entornos virtuales, cachés ni respaldos.

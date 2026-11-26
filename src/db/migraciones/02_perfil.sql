-- Migración: agrega la foto de perfil a una base de datos que YA existe.
-- Está en una subcarpeta a propósito: Docker solo ejecuta automáticamente los .sql de bd/,
-- y en una base nueva 01_esquema.sql ya incluye esta columna (se duplicaría y fallaría).
--
-- Ejecútala una sola vez (PowerShell, con el contenedor encendido):
--   docker exec -it iot_frontend_mysql mysql -u root -p iot_frontend -e "ALTER TABLE cuentas ADD COLUMN foto VARCHAR(64) NULL AFTER estado;"
-- (te pide el MYSQL_ROOT_PASSWORD de tu .env). Conserva todas las cuentas y dispositivos.

ALTER TABLE cuentas
    ADD COLUMN foto VARCHAR(64) NULL AFTER estado;

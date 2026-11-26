-- Esquema de la base de datos del frontend IoT (MySQL 8.4).
-- Docker lo ejecuta solo la PRIMERA vez que se crea el volumen.
-- Para volver a ejecutarlo: docker compose down -v && docker compose up -d

SET NAMES utf8mb4;

-- Todas las personas que inician sesión: master, administradores y usuarios.
-- Los formularios de "Usuarios" y "Administradores" escriben aquí; solo cambia `rol`.
CREATE TABLE IF NOT EXISTS cuentas (
    id               INT UNSIGNED NOT NULL AUTO_INCREMENT,
    rol              ENUM('master', 'administrador', 'usuario') NOT NULL,
    nombre_completo  VARCHAR(100) NOT NULL,
    correo           VARCHAR(254) NOT NULL,
    usuario          VARCHAR(30)  NOT NULL,
    -- Hash Argon2id. La contraseña en claro nunca se guarda.
    contrasena_hash  VARCHAR(255) NOT NULL,
    -- 0 = contraseña provisional (debe cambiarla en el primer inicio de sesión)
    -- 1 = ya la cambió
    contra_cambiada  TINYINT(1)   NOT NULL DEFAULT 0,
    -- 'pendiente' al registrar; solo 'activo' puede iniciar sesión.
    estado           ENUM('activo', 'pendiente', 'inactivo') NOT NULL DEFAULT 'pendiente',
    creado_por       INT UNSIGNED NULL,
    fecha_registro   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_cuentas_correo (correo),
    UNIQUE KEY uq_cuentas_usuario (usuario),
    KEY ix_cuentas_rol_estado (rol, estado),
    CONSTRAINT fk_cuentas_creado_por FOREIGN KEY (creado_por)
        REFERENCES cuentas (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Formulario de "Dispositivos".
CREATE TABLE IF NOT EXISTS dispositivos (
    id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
    identificador  VARCHAR(30)  NOT NULL,
    zona           VARCHAR(50)  NOT NULL,
    descripcion    VARCHAR(255) NOT NULL,
    estado         ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    creado_por     INT UNSIGNED NULL,
    fecha_registro TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispositivos_identificador (identificador),
    KEY ix_dispositivos_zona (zona),
    CONSTRAINT fk_dispositivos_creado_por FOREIGN KEY (creado_por)
        REFERENCES cuentas (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

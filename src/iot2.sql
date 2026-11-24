-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1:3306
-- Tiempo de generación: 19-11-2026 a las 03:07:27
-- Versión del servidor: 8.4.7
-- Versión de PHP: 8.3.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `iot2`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `administradores`
--

DROP TABLE IF EXISTS `administradores`;
CREATE TABLE IF NOT EXISTS `administradores` (
  `id_priv` int UNSIGNED NOT NULL,
  `id_pub` int UNSIGNED NOT NULL,
  `usuario` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '0',
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `es_master` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_priv`),
  UNIQUE KEY `id_pub` (`id_pub`)
) ;

--
-- Volcado de datos para la tabla `administradores`
--

INSERT INTO `administradores` (`id_priv`, `id_pub`, `usuario`, `activo`, `fecha_registro`, `es_master`) VALUES
(1085525971, 1837871152, 'juanjo2002', 1, '2026-11-08 19:32:03', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `administradores_nombres`
--

DROP TABLE IF EXISTS `administradores_nombres`;
CREATE TABLE IF NOT EXISTS `administradores_nombres` (
  `id_priv` int UNSIGNED NOT NULL,
  `nombre` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `apellido` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_priv`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `administradores_nombres`
--

INSERT INTO `administradores_nombres` (`id_priv`, `nombre`, `apellido`) VALUES
(1085525971, 'Juan Jose', 'Lopez Guevara');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `contrasenas`
--

DROP TABLE IF EXISTS `contrasenas`;
CREATE TABLE IF NOT EXISTS `contrasenas` (
  `id_priv` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `id_priv_usuario` int UNSIGNED DEFAULT NULL,
  `id_priv_admin` int UNSIGNED DEFAULT NULL,
  `contrasena` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `contra_cambiada` int NOT NULL DEFAULT '0',
  `llave_hmac_cifrada` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id_priv`),
  UNIQUE KEY `uq_contrasenas_usuario` (`id_priv_usuario`),
  UNIQUE KEY `uq_contrasenas_admin` (`id_priv_admin`)
) ;

--
-- Volcado de datos para la tabla `contrasenas`
--

INSERT INTO `contrasenas` (`id_priv`, `id_priv_usuario`, `id_priv_admin`, `contrasena`, `contra_cambiada`, `llave_hmac_cifrada`) VALUES
(3, NULL, 1085525971, '$argon2id$v=19$m=65536,t=3,p=4$ZslXwisDH0XpyxbGGUoAyA$mfX/mTA0YPGVclIYOrOqXLRsO/qhaRww06XzPqgjLbc', 0, NULL),
(4, 3273750253, NULL, '$argon2id$v=19$m=65536,t=3,p=4$15UWX0o0aZ9/XAzI8gZpoQ$CZBsJHEve3hf2BkaAYiMO9Ql7wD0ImUXGdt94VTo7rY', 0, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `correos`
--

DROP TABLE IF EXISTS `correos`;
CREATE TABLE IF NOT EXISTS `correos` (
  `id_priv` int UNSIGNED NOT NULL AUTO_INCREMENT,
  `id_priv_usuario` int UNSIGNED DEFAULT NULL,
  `id_priv_admin` int UNSIGNED DEFAULT NULL,
  `correo` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_priv`),
  UNIQUE KEY `uq_correos_correo` (`correo`),
  UNIQUE KEY `uq_correos_usuario` (`id_priv_usuario`),
  UNIQUE KEY `uq_correos_admin` (`id_priv_admin`)
) ;

--
-- Volcado de datos para la tabla `correos`
--

INSERT INTO `correos` (`id_priv`, `id_priv_usuario`, `id_priv_admin`, `correo`) VALUES
(1, NULL, 1085525971, 'juanjo2002lopez@gmail.com'),
(2, 3273750253, NULL, 'miskamuska2011@gmail.com');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `dispositivos`
--

DROP TABLE IF EXISTS `dispositivos`;
CREATE TABLE IF NOT EXISTS `dispositivos` (
  `id_priv` int UNSIGNED NOT NULL,
  `id_pub` int UNSIGNED NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_priv`),
  UNIQUE KEY `id_pub` (`id_pub`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `dispositivos_info`
--

DROP TABLE IF EXISTS `dispositivos_info`;
CREATE TABLE IF NOT EXISTS `dispositivos_info` (
  `id_priv` int UNSIGNED NOT NULL,
  `nombre` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_disp` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_priv`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `dispositivos_registrados`
--

DROP TABLE IF EXISTS `dispositivos_registrados`;
CREATE TABLE IF NOT EXISTS `dispositivos_registrados` (
  `id_priv_admin` int UNSIGNED NOT NULL,
  `id_priv_dispositivo` int UNSIGNED NOT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_priv_admin`,`id_priv_dispositivo`),
  KEY `fk_registro_dispositivo` (`id_priv_dispositivo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `dispositivos_seguridad`
--

DROP TABLE IF EXISTS `dispositivos_seguridad`;
CREATE TABLE IF NOT EXISTS `dispositivos_seguridad` (
  `id_priv` int UNSIGNED NOT NULL,
  `llave_hmac_cifrada` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id_priv`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_priv` int UNSIGNED NOT NULL,
  `id_pub` int UNSIGNED NOT NULL,
  `usuario` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '0',
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_priv`),
  UNIQUE KEY `id_pub` (`id_pub`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id_priv`, `id_pub`, `usuario`, `activo`, `fecha_registro`) VALUES
(3273750253, 4219889901, 'miskamuska2011', 1, '2026-11-08 19:35:20');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios_nombres`
--

DROP TABLE IF EXISTS `usuarios_nombres`;
CREATE TABLE IF NOT EXISTS `usuarios_nombres` (
  `id_priv` int UNSIGNED NOT NULL,
  `nombre` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `apellido` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_priv`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios_nombres`
--

INSERT INTO `usuarios_nombres` (`id_priv`, `nombre`, `apellido`) VALUES
(3273750253, 'Wilmer', 'Hernandez Herrera');

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `administradores_nombres`
--
ALTER TABLE `administradores_nombres`
  ADD CONSTRAINT `fk_adm_nombres_admin` FOREIGN KEY (`id_priv`) REFERENCES `administradores` (`id_priv`) ON DELETE CASCADE;

--
-- Filtros para la tabla `contrasenas`
--
ALTER TABLE `contrasenas`
  ADD CONSTRAINT `fk_contrasenas_admin` FOREIGN KEY (`id_priv_admin`) REFERENCES `administradores` (`id_priv`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_contrasenas_usuario` FOREIGN KEY (`id_priv_usuario`) REFERENCES `usuarios` (`id_priv`) ON DELETE CASCADE;

--
-- Filtros para la tabla `correos`
--
ALTER TABLE `correos`
  ADD CONSTRAINT `fk_correos_admin` FOREIGN KEY (`id_priv_admin`) REFERENCES `administradores` (`id_priv`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_correos_usuario` FOREIGN KEY (`id_priv_usuario`) REFERENCES `usuarios` (`id_priv`) ON DELETE CASCADE;

--
-- Filtros para la tabla `dispositivos_info`
--
ALTER TABLE `dispositivos_info`
  ADD CONSTRAINT `fk_disp_info_identidad` FOREIGN KEY (`id_priv`) REFERENCES `dispositivos` (`id_priv`) ON DELETE CASCADE;

--
-- Filtros para la tabla `dispositivos_registrados`
--
ALTER TABLE `dispositivos_registrados`
  ADD CONSTRAINT `fk_registro_admin` FOREIGN KEY (`id_priv_admin`) REFERENCES `administradores` (`id_priv`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_registro_dispositivo` FOREIGN KEY (`id_priv_dispositivo`) REFERENCES `dispositivos` (`id_priv`) ON DELETE CASCADE;

--
-- Filtros para la tabla `dispositivos_seguridad`
--
ALTER TABLE `dispositivos_seguridad`
  ADD CONSTRAINT `fk_disp_seguridad_identidad` FOREIGN KEY (`id_priv`) REFERENCES `dispositivos` (`id_priv`) ON DELETE CASCADE;

--
-- Filtros para la tabla `usuarios_nombres`
--
ALTER TABLE `usuarios_nombres`
  ADD CONSTRAINT `fk_usu_nombres_usuarios` FOREIGN KEY (`id_priv`) REFERENCES `usuarios` (`id_priv`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

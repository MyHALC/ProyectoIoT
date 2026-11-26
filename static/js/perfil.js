(function () {
    const $ = id => document.getElementById(id);

    const MAX_FOTO = 2 * 1024 * 1024;
    const TIPOS_FOTO = ["image/jpeg", "image/png", "image/webp"];
    const ROLES = {
        master: "Administrador master",
        administrador: "Administrador",
        usuario: "Usuario"
    };

    function mensaje(elemento, texto, tipo) {
        elemento.textContent = texto;
        elemento.className = "profile-message" + (tipo ? " " + tipo : "");
    }

    // Muestra la foto o, si no hay, la inicial del nombre.
    function pintarAvatar(contenedor, fotoUrl, inicial) {
        contenedor.textContent = "";
        if (fotoUrl) {
            const imagen = document.createElement("img");
            imagen.src = fotoUrl;
            imagen.alt = "";
            contenedor.appendChild(imagen);
        } else {
            contenedor.textContent = inicial;
        }
    }

    function pintarFoto(perfil) {
        const inicial = (perfil.nombre_completo || "U").charAt(0).toUpperCase();
        pintarAvatar($("fotoGrande"), perfil.foto_url, inicial);

        // El avatar del menú lateral se actualiza sin recargar la página.
        const lateral = document.querySelector(".sidebar .avatar");
        if (lateral) pintarAvatar(lateral, perfil.foto_url, inicial);

        $("botonQuitarFoto").hidden = !perfil.foto_url;
    }

    function pintarPerfil(perfil) {
        pintarFoto(perfil);

        $("perfilNombre").textContent = perfil.nombre_completo;
        $("perfilRol").textContent = ROLES[perfil.rol] || perfil.rol;
        $("perfilCorreo").textContent = perfil.correo;

        const estado = ESTADOS[perfil.estado] || ESTADOS.inactivo; // ESTADOS viene de api.js
        $("perfilEstado").textContent = estado.texto;
        $("perfilEstado").className = "status-badge " + estado.clase;

        const fecha = new Date(perfil.fecha_registro);
        $("perfilFecha").textContent = isNaN(fecha)
            ? "—"
            : fecha.toLocaleDateString("es-MX", { year: "numeric", month: "long", day: "numeric" });

        $("perfilNombreCompleto").value = perfil.nombre_completo;
        $("perfilCorreoInput").value = perfil.correo;
        $("perfilUsuario").value = perfil.usuario;
    }

    // Deshabilita el botón mientras se envía para evitar envíos dobles.
    async function enviando(boton, accion) {
        boton.disabled = true;
        try {
            await accion();
        } finally {
            boton.disabled = false;
        }
    }

    // ---------------------------------------------------------------- foto

    $("botonFoto").addEventListener("click", () => $("inputFoto").click());

    $("inputFoto").addEventListener("change", async () => {
        const entrada = $("inputFoto");
        const archivo = entrada.files[0];
        if (!archivo) return;

        const salida = $("mensajeFoto");
        if (!TIPOS_FOTO.includes(archivo.type)) {
            mensaje(salida, "Usa una imagen JPG, PNG o WebP.", "error");
        } else if (archivo.size > MAX_FOTO) {
            mensaje(salida, "La imagen no debe pasar de 2 MB.", "error");
        } else {
            await enviando($("botonFoto"), async () => {
                try {
                    const datos = new FormData();
                    datos.append("foto", archivo);
                    const respuesta = await api("/api/perfil/foto", { metodo: "POST", cuerpo: datos });
                    pintarFoto({
                        nombre_completo: $("perfilNombre").textContent,
                        foto_url: respuesta.foto_url
                    });
                    mensaje(salida, "Foto actualizada.", "ok");
                } catch (error) {
                    mensaje(salida, error.message, "error");
                }
            });
        }
        entrada.value = ""; // permite elegir de nuevo el mismo archivo
    });

    $("botonQuitarFoto").addEventListener("click", async () => {
        if (!window.confirm("¿Quitar tu foto de perfil?")) return;
        await enviando($("botonQuitarFoto"), async () => {
            try {
                await api("/api/perfil/foto", { metodo: "DELETE", cuerpo: {} });
                pintarFoto({ nombre_completo: $("perfilNombre").textContent, foto_url: null });
                mensaje($("mensajeFoto"), "Foto eliminada.", "ok");
            } catch (error) {
                mensaje($("mensajeFoto"), error.message, "error");
            }
        });
    });

    // ------------------------------------------------------ nombre de usuario

    $("formUsuario").addEventListener("submit", async evento => {
        evento.preventDefault();
        const salida = $("mensajeUsuario");
        const usuario = $("perfilUsuario").value.trim();

        if (!/^[A-Za-z0-9._-]{3,30}$/.test(usuario)) {
            mensaje(salida, "El usuario solo admite letras, números, punto, guion y guion bajo (3 a 30).", "error");
            return;
        }
        if (!$("usuarioContrasena").value) {
            mensaje(salida, "Escribe tu contraseña actual.", "error");
            return;
        }

        await enviando(evento.submitter || evento.target.querySelector("button[type=submit]"), async () => {
            try {
                const perfil = await api("/api/perfil", {
                    metodo: "PATCH",
                    cuerpo: { usuario, contrasena_actual: $("usuarioContrasena").value }
                });
                pintarPerfil(perfil);
                $("usuarioContrasena").value = "";
                mensaje(salida, "Usuario actualizado. Desde ahora inicia sesión con " + perfil.usuario + ".", "ok");
            } catch (error) {
                mensaje(salida, error.message, "error");
            }
        });
    });

    // ------------------------------------------------------------- contraseña

    $("formContrasena").addEventListener("submit", async evento => {
        evento.preventDefault();
        const salida = $("mensajeContrasena");
        const actual = $("contrasenaActual").value;
        const nueva = $("contrasenaNueva").value;
        const confirmar = $("contrasenaConfirmar").value;

        if (!actual) {
            mensaje(salida, "Escribe tu contraseña actual.", "error");
        } else if (nueva.length < 8 || nueva.length > 128) {
            mensaje(salida, "La contraseña nueva debe tener entre 8 y 128 caracteres.", "error");
        } else if (nueva !== confirmar) {
            mensaje(salida, "Las contraseñas nuevas no coinciden.", "error");
        } else {
            await enviando(evento.submitter || evento.target.querySelector("button[type=submit]"), async () => {
                try {
                    await api("/api/perfil/contrasena", {
                        metodo: "POST",
                        cuerpo: { contrasena_actual: actual, contrasena_nueva: nueva }
                    });
                    evento.target.reset();
                    mensaje(salida, "Contraseña actualizada.", "ok");
                } catch (error) {
                    mensaje(salida, error.message, "error");
                }
            });
        }
    });

    // ------------------------------------------------------------------ inicio

    api("/api/perfil")
        .then(pintarPerfil)
        .catch(error => mensaje($("mensajeFoto"), error.message, "error"));
})();

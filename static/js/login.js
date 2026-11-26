const formularioLogin = document.getElementById("loginForm");

const modal = document.getElementById("modal");
const mensaje = document.getElementById("mensaje");
const icono = document.getElementById("icono");
const cerrarModal = document.getElementById("cerrarModal");

// Misma dirección que la página (Flask). Para usar otro backend, cambia esta URL.
const API = "/api/usuarios";

const vistaLogin = document.getElementById("vistaLogin");
const vistaCambio = document.getElementById("vistaCambio");

const cambioForm = document.getElementById("cambioForm");

let cuentaCambio = null;

let destinoDespuesDelLogin = null;

// Mostrar mensajes
function mostrarMensaje(estado, texto) {
    if (estado === "exito") {
        icono.textContent = "✅";
    } else {
        icono.textContent = "❌";
    }

    mensaje.textContent = texto;
    modal.style.display = "flex";
}

// Cerrar modal y continuar si el login fue exitoso
cerrarModal.addEventListener("click", function () {
    modal.style.display = "none";

    if (destinoDespuesDelLogin) {
        window.location.href = destinoDespuesDelLogin;
    }
});

// Enviar solicitud a FastAPI
async function enviarSolicitud(url, datos) {
    try {
        const respuesta = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            const detalle = Array.isArray(resultado.detail)
                ? resultado.detail.map(error => error.msg).join(", ")
                : resultado.detail;

            mostrarMensaje(
                "error",
                detalle || "No fue posible procesar la solicitud."
            );

            return null;
        }

        return resultado;

    } catch (error) {
        console.error("Error:", error);

        mostrarMensaje(
            "error",
            "No se pudo conectar con el servidor. Verifica que FastAPI esté funcionando."
        );

        return null;
    }
}

// Mostrar la vista correspondiente
function mostrarVista(vista) {
    vistaLogin.style.display = "none";
    vistaCambio.style.display = "none";

    vista.style.display = "block";
}

// Regresar al login
function volverAlLogin() {
    cuentaCambio = null;
    cambioForm.reset();

    mostrarVista(vistaLogin);
}

// Inicio de sesión
formularioLogin.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    const usuario = document.getElementById("usuario").value.trim();
    const contraseña = document.getElementById("contraseña").value;

    const resultado = await enviarSolicitud(`${API}/login/`, {
        usuario: usuario,
        contraseña: contraseña
    });

    if (!resultado) {
        return;
    }

    if (resultado.estado !== "exito" || !resultado.usuario) {
        mostrarMensaje(
            "error",
            resultado.mensaje || "No fue posible iniciar sesión."
        );
        return;
    }

    const datosUsuario = resultado.usuario;
    // Detectar si FastAPI indica que debe cambiar su contraseña.
    if (resultado.requiere_cambio_contrasena ||
        datosUsuario.requiere_cambio_contrasena) {

        cuentaCambio = true;

        formularioLogin.reset();
        mostrarVista(vistaCambio);
        return;
    }

    // Guardar únicamente datos informativos, nunca la contraseña.
    sessionStorage.setItem("usuario", JSON.stringify(datosUsuario));

    // Determinar la pagina según el rol devuelto por FastAPI.
    if (datosUsuario.rol === "master") {
        destinoDespuesDelLogin = "/master";
    } else if (datosUsuario.rol === "administrador") {
        destinoDespuesDelLogin = "/admin";
    } else if (datosUsuario.rol === "usuario") {
        destinoDespuesDelLogin = "/usuario";
    } else {
        sessionStorage.removeItem("usuario");

        mostrarMensaje(
            "error",
            "El tipo de cuenta no tiene un panel asignado."
        );

        return;
    }

    mostrarMensaje(
        "exito",
        `¡Bienvenido/a, ${datosUsuario.nombre_completo}!`
    );
});

// Cambio de contraseña provisional
cambioForm.addEventListener("submit", async function (evento) {

    evento.preventDefault();

    if (!cuentaCambio) {
        volverAlLogin();
        return;
    }

    const nueva = document.getElementById("camNueva").value;
    const confirmar = document.getElementById("camConfirmar").value;

    if (nueva !== confirmar) {
        alert("Las contraseñas no coinciden");
        return;
    }

    try {

        const respuesta = await fetch("/api/cambiar-contrasena", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ contrasena_nueva: nueva })
        });

        const datos = await respuesta.json();

        if (respuesta.ok) {

            alert("Contraseña actualizada. Inicia sesión nuevamente.");

            volverAlLogin();

        } else {

            alert(datos.detail || "No se pudo cambiar la contraseña");
            if (respuesta.status === 401) { volverAlLogin(); }

        }

    } catch (error) {

    console.error("ERROR AL CAMBIAR CONTRASEÑA:", error);

    alert("Error de conexión: " + error.message);

    }

});

// Cancelar el cambio: se cierra la sesión limitada.
document.getElementById("cancelarCambio").addEventListener("click", async function () {
    try {
        await fetch("/api/salir", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: "{}"
        });
    } finally {
        volverAlLogin();
    }
});

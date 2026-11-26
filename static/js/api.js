// Ayudantes compartidos por las pantallas de gestión.

async function api(url, { metodo = "GET", cuerpo } = {}) {
    const config = { method: metodo, credentials: "same-origin", headers: {} };

    if (cuerpo !== undefined) {
        config.headers["X-Requested-With"] = "XMLHttpRequest";
        config.body = cuerpo;
    } else if (cuerpo !== undefined) {
        config.headers["Content-Type"] = "application/json";
        config.body = JSON.stringify(cuerpo);
    }

    let respuesta;
    try {
        respuesta = await fetch(url, config);
    } catch (error) {
        throw new Error("No se pudo conectar con el servidor.");
    }

    let datos = null;
    try {
        datos = await respuesta.json();
    } catch (error) {
        // La respuesta no traía JSON.
    }

    if (respuesta.status === 401) {
        sessionStorage.clear();
        window.location.href = "/";
        throw new Error("Tu sesión terminó. Inicia sesión de nuevo.");
    }

    if (!respuesta.ok) {
        const detalle = datos && datos.detail;
        throw new Error(
            (Array.isArray(detalle) ? detalle.map(e => e.msg).join(", ") : detalle)
            || "No fue posible procesar la solicitud."
        );
    }

    return datos;
}

// Todo se escribe con textContent para que nada de lo guardado se interprete como HTML.
function celda(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
}

const ESTADOS = {
    activo: { texto: "Activo", clase: "active-status" },
    pendiente: { texto: "Pendiente", clase: "pending-status" },
    inactivo: { texto: "Inactivo", clase: "inactive-status" }
};

function celdaEstado(estado) {
    const td = document.createElement("td");
    const etiqueta = document.createElement("span");
    const info = ESTADOS[estado] || ESTADOS.inactivo;

    etiqueta.className = `status-badge ${info.clase}`;
    etiqueta.textContent = info.texto;
    td.appendChild(etiqueta);
    return td;
}

function celdaAccion(estado, alHacerClic) {
    const td = document.createElement("td");
    const boton = document.createElement("button");

    boton.className = "table-button";
    boton.textContent = estado === "activo" ? "Desactivar" : "Activar";
    boton.onclick = async () => {
        boton.disabled = true;
        try {
            await alHacerClic();
        } catch (error) {
            alert(error.message);
            boton.disabled = false;
        }
    };

    td.appendChild(boton);
    return td;
}

function filaVacia(columnas, texto) {
    const tr = document.createElement("tr");
    const td = celda(texto);
    td.colSpan = columnas;
    tr.appendChild(td);
    return tr;
}

function pad(numero) {
    return String(numero).padStart(2, "0");
}

function filtrarTabla(entrada, tabla) {
    entrada.addEventListener("input", () => {
        const busqueda = entrada.value.toLowerCase();

        tabla.querySelectorAll("tr").forEach(fila => {
            fila.style.display = fila.textContent
                .toLowerCase().includes(busqueda) ? "" : "none";
        });
    });
}

async function cerrarSesion() {
    try {
        await fetch("/api/salir", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: "{}"
        });
    } catch (error) {
        // Aun sin respuesta del servidor se limpia el navegador.
    }

    sessionStorage.clear();
    window.location.href = "/";
}

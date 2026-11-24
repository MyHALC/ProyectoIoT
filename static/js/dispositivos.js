// Pantalla de Dispositivos.

(function () {
    const porId = id => document.getElementById(id);

    const modal = porId("modalRegistro");
    const formulario = porId("formDispositivo");
    const tabla = porId("tablaDispositivos");

    let dispositivos = [];

    async function cargar() {
        try {
            dispositivos = await api("/api/dispositivos");
            pintar();
        } catch (error) {
            tabla.replaceChildren(filaVacia(5, error.message));
        }
    }

    function pintar() {
        tabla.replaceChildren();

        if (dispositivos.length === 0) {
            tabla.appendChild(filaVacia(5, "Todavía no hay registros."));
        }

        dispositivos.forEach(dispositivo => {
            const fila = document.createElement("tr");

            fila.appendChild(celda(dispositivo.identificador));
            fila.appendChild(celda(dispositivo.zona));
            fila.appendChild(celda(dispositivo.descripcion));
            fila.appendChild(celdaEstado(dispositivo.estado));
            fila.appendChild(celdaAccion(dispositivo.estado,
                () => cambiarEstado(dispositivo)));

            tabla.appendChild(fila);
        });

        actualizarContadores();
    }

    function actualizarContadores() {
        const activos = dispositivos.filter(d => d.estado === "activo").length;
        const zonas = new Set(dispositivos.map(d => d.zona.toLowerCase()));

        porId("totalDispositivos").textContent = pad(dispositivos.length);
        porId("totalActivos").textContent = pad(activos);
        porId("totalInactivos").textContent = pad(dispositivos.length - activos);
        porId("totalZonas").textContent = pad(zonas.size);
    }

    async function cambiarEstado(dispositivo) {
        const nuevo = dispositivo.estado === "activo" ? "inactivo" : "activo";

        await api(`/api/dispositivos/${dispositivo.id}/estado`, {
            metodo: "PATCH",
            cuerpo: { estado: nuevo }
        });

        dispositivo.estado = nuevo;
        pintar();
    }

    formulario.addEventListener("submit", async evento => {
        evento.preventDefault();

        const enviar = formulario.querySelector("button[type='submit']");
        enviar.disabled = true;

        try {
            const nuevo = await api("/api/dispositivos", {
                metodo: "POST",
                cuerpo: {
                    identificador: porId("identificador").value.trim(),
                    zona: porId("zona").value.trim(),
                    descripcion: porId("descripcion").value.trim()
                }
            });

            dispositivos.push(nuevo);
            pintar();
            formulario.reset();
            cerrarFormulario();
        } catch (error) {
            alert(error.message);
        } finally {
            enviar.disabled = false;
        }
    });

    function cerrarFormulario() {
        modal.style.display = "none";
    }

    porId("abrirFormulario").onclick = () => {
        modal.style.display = "flex";
    };
    porId("cerrarFormulario").onclick = cerrarFormulario;
    porId("cancelarFormulario").onclick = cerrarFormulario;

    filtrarTabla(porId("buscarDispositivo"), tabla);
    cargar();
})();

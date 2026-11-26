// Pantallas de Usuarios y Administradores. Cada página define antes window.GESTION:
//   { rol, tabla, total, buscar, formulario }

(function () {
    const cfg = window.GESTION;
    const porId = id => document.getElementById(id);

    const modal = porId("modalRegistro");
    const formulario = porId(cfg.formulario);
    const tabla = porId(cfg.tabla);
    const campoContrasena = porId("contrasenaProvisional");

    let cuentas = [];

    // ---------- contraseña provisional (se genera en el navegador) ----------

    function generarContrasena() {
        const caracteres =
            "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%";

        const valores = new Uint32Array(16);
        crypto.getRandomValues(valores);

        campoContrasena.value = Array.from(valores)
            .map(valor => caracteres[valor % caracteres.length])
            .join("");
    }

    // ---------- lectura ----------

    async function cargar() {
        try {
            cuentas = await api(`/api/cuentas?rol=${cfg.rol}`);
            pintar();
        } catch (error) {
            tabla.replaceChildren(filaVacia(5, error.message));
        }
    }

    function pintar() {
        tabla.replaceChildren();

        if (cuentas.length === 0) {
            tabla.appendChild(filaVacia(5, "Todavía no hay registros."));
        }

        cuentas.forEach(cuenta => {
            const fila = document.createElement("tr");

            fila.appendChild(celda(cuenta.nombre_completo));
            fila.appendChild(celda(cuenta.usuario));
            fila.appendChild(celda(cuenta.correo));
            fila.appendChild(celdaEstado(cuenta.estado));
            fila.appendChild(celdaAccion(cuenta.estado, () => cambiarEstado(cuenta)));

            tabla.appendChild(fila);
        });

        actualizarContadores();
    }

    function actualizarContadores() {
        const contar = estado => cuentas.filter(c => c.estado === estado).length;

        porId(cfg.total).textContent = pad(cuentas.length);
        porId("totalActivos").textContent = pad(contar("activo"));
        porId("totalPendientes").textContent = pad(contar("pendiente"));
        porId("totalInactivos").textContent = pad(contar("inactivo"));
    }

    // ---------- escritura ----------

    async function cambiarEstado(cuenta) {
        const nuevo = cuenta.estado === "activo" ? "inactivo" : "activo";

        await api(`/api/cuentas/${cuenta.id}/estado`, {
            metodo: "PATCH",
            cuerpo: { estado: nuevo }
        });

        cuenta.estado = nuevo;
        pintar();
    }

    formulario.addEventListener("submit", async evento => {
        evento.preventDefault();

        const enviar = formulario.querySelector("button[type='submit']");
        enviar.disabled = true;

        try {
            const nueva = await api("/api/cuentas", {
                metodo: "POST",
                cuerpo: {
                    rol: cfg.rol,
                    nombre_completo: porId("nombreCompleto").value.trim(),
                    correo: porId("correo").value.trim(),
                    usuario: porId("nombreUsuario").value.trim(),
                    contrasena: campoContrasena.value
                }
            });

            cuentas.push(nueva);
            pintar();
            formulario.reset();
            cerrarFormulario();

            alert(
                "Cuenta registrada en estado Pendiente.\n\n" +
                (nueva.correo_enviado
                    ? "Se envió la contraseña provisional al correo. "
                    : "No se pudo enviar el correo; entrega la contraseña provisional tú mismo, ya no se puede consultar. ") +
                "Para que pueda iniciar sesión, actívala desde la tabla."
            );
        } catch (error) {
            alert(error.message);
        } finally {
            enviar.disabled = false;
        }
    });

    // ---------- ventana de registro ----------

    function cerrarFormulario() {
        modal.style.display = "none";
    }

    porId("abrirFormulario").onclick = () => {
        generarContrasena();
        modal.style.display = "flex";
    };
    porId("cerrarFormulario").onclick = cerrarFormulario;
    porId("cancelarFormulario").onclick = cerrarFormulario;
    porId("generarContrasena").onclick = generarContrasena;

    porId("copiarContrasena").onclick = async () => {
        try {
            await navigator.clipboard.writeText(campoContrasena.value);
            alert("Contraseña provisional copiada.");
        } catch (error) {
            alert("No fue posible copiarla. Puedes seleccionarla manualmente.");
        }
    };

    filtrarTabla(porId(cfg.buscar), tabla);
    cargar();
})();

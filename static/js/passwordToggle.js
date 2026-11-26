// Agrega un botón "ver / ocultar" a TODOS los campos de contraseña de la página.
// No hay que tocar el HTML: basta con cargar este script. También funciona con
// campos que se agreguen después (por ejemplo dentro de una ventana emergente).

(function () {
    const OJO = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';

    const OJO_TACHADO = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a19.8 19.8 0 0 1 5.06-5.94"/>' +
        '<path d="M9.9 4.24A10.9 10.9 0 0 1 12 4c7 0 11 7 11 7a19.7 19.7 0 0 1-3.17 4.19"/>' +
        '<path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M1 1l22 22"/></svg>';

    function mostrar(campo, boton, visible) {
        campo.type = visible ? "text" : "password";
        boton.setAttribute("aria-pressed", String(visible));
        boton.setAttribute("aria-label", visible ? "Ocultar contraseña" : "Mostrar contraseña");
        boton.title = boton.getAttribute("aria-label");
        boton.innerHTML = visible ? OJO_TACHADO : OJO;
    }

    function mejorar(campo) {
        if (campo.dataset.verOcultar) return;
        campo.dataset.verOcultar = "1";

        const envoltura = document.createElement("span");
        envoltura.className = "pw-field";
        campo.parentNode.insertBefore(envoltura, campo);
        envoltura.appendChild(campo);
        campo.classList.add("pw-input");

        const boton = document.createElement("button");
        boton.type = "button"; // para que no envíe el formulario
        boton.className = "pw-toggle";
        mostrar(campo, boton, false);
        boton.addEventListener("click", () => mostrar(campo, boton, campo.type === "password"));
        envoltura.appendChild(boton);

        // Al enviar el formulario la contraseña vuelve a quedar oculta.
        if (campo.form) {
            campo.form.addEventListener("submit", () => mostrar(campo, boton, false));
        }
    }

    function revisar(raiz) {
        raiz.querySelectorAll('input[type="password"]').forEach(mejorar);
    }

    function iniciar() {
        revisar(document);
        new MutationObserver(cambios => {
            cambios.forEach(c => c.addedNodes.forEach(nodo => {
                if (nodo.nodeType !== 1) return;
                if (nodo.matches('input[type="password"]')) mejorar(nodo);
                else revisar(nodo);
            }));
        }).observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();

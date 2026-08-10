// Código limpio sin bucles pesados ni funciones redundantes
(function() {
    "use strict";
    
    const inicializarPremios = () => {
        const contenedor = document.querySelector(".contenedor-premios");
        if (!contenedor) return; // Retorno inmediato si no existe (evita errores en consola)

        // Usamos delegación de eventos en el contenedor padre (Mucho más rápido que un bucle por cada tarjeta)
        contenedor.addEventListener("click", (evento) => {
            const tarjeta = evento.target.closest(".tarjeta-premio");
            if (!tarjeta) return;

            // Quita la clase activa de cualquier otra tarjeta
            contenedor.querySelectorAll(".tarjeta-premio.activa").forEach(t => {
                if (t !== tarjeta) t.classList.remove("activa");
            });

            // Alterna la clase en la tarjeta clickeada
            tarjeta.classList.toggle("activa");
        });
    };

    // Se ejecuta tan pronto como el HTML está listo, sin esperar imágenes pesadas
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializarPremios);
    } else {
        inicializarPremios();
    }
})();

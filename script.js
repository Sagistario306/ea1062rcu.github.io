document.addEventListener("DOMContentLoaded", () => {
    
    // ---------------------------------------------------------
    // SECCIÓN 1: ANIMACIÓN AL HACER SCROLL (YA CONFIGURADA)
    // ---------------------------------------------------------
    const tarjetas = document.querySelectorAll(".tarjeta-premio");
    const opcionesScroll = { root: null, rootMargin: "0px", threshold: 0.15 };

    const aparecerAlHacerScroll = new IntersectionObserver((entradas, observador) => {
        entradas.forEach(entrada => {
            if (entrada.isIntersecting) {
                entrada.target.classList.add("tarjeta-visible");
                observador.unobserve(entrada.target);
            }
        });
    }, opcionesScroll);

    tarjetas.forEach(tarjeta => aparecerAlHacerScroll.observe(tarjeta));

    // ---------------------------------------------------------
    // SECCIÓN 2: CONTROL DE LIGHTBOX EFICIENTE (NUEVO)
    // ---------------------------------------------------------
    const modal = document.getElementById("lightbox-modal");
    const imgModal = document.getElementById("lightbox-img");
    const botonCerrar = document.querySelector(".lightbox-cerrar");
    const contenedorPrincipal = document.querySelector(".contenedor-premios");

    if (modal && imgModal && contenedorPrincipal) {
        
        // DELEGACIÓN DE EVENTOS: Escuchamos clics en el contenedor de premios.
        // Es mil veces más rápido que asignarle un evento "click" a cada una de las 87 fotos por separado.
        contenedorPrincipal.addEventListener("click", (evento) => {
            // Verificamos si lo que el usuario cliqueó es una imagen dentro de una galería
            const miniatura = evento.target.closest(".galeria-tarjeta img");
            if (!miniatura) return; // Si no es una foto de galería, ignoramos el clic

            // Extraemos la ruta (src) y el texto alternativo (alt) de la miniatura cliqueada
            imgModal.src = miniatura.src;
            imgModal.alt = miniatura.alt;
            
            // Mostramos el modal flotante
            modal.classList.add("activo");
            document.body.style.overflow = "hidden"; // Bloquea el scroll del fondo mientras se ve el diploma
        });

        // Función para cerrar el Lightbox limpiamente
        const cerrarLightbox = () => {
            modal.classList.remove("activo");
            document.body.style.overflow = ""; // Devuelve el scroll normal al sitio web
            // Limpiamos la ruta después de cerrar para ahorrar memoria
            setTimeout(() => { imgModal.src = ""; }, 300); 
        };

        // Cerrar al pulsar el botón de la equis (X)
        botonCerrar.addEventListener("click", cerrarLightbox);

        // Cerrar automáticamente si el usuario hace clic afuera de la foto (en el fondo oscuro)
        modal.addEventListener("click", (evento) => {
            if (evento.target === modal) {
                cerrarLightbox();
            }
        });

        // Accesibilidad avanzada: Cerrar al pulsar la tecla "Escape" (ESC) en el teclado
        document.addEventListener("keydown", (evento) => {
            if (evento.key === "Escape" && modal.classList.contains("activo")) {
                cerrarLightbox();
            }
        });
    }
});

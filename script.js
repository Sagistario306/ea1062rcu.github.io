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
    // SECCIÓN 2: CONTROL DE LIGHTBOX CON NAVEGACIÓN EN SERIE
    // ---------------------------------------------------------
    const modal = document.getElementById("lightbox-modal");
    const imgModal = document.getElementById("lightbox-img");
    const botonCerrar = document.querySelector(".lightbox-cerrar");
    const flechaAnt = document.querySelector(".lightbox-flecha.anterior");
    const flechaSig = document.querySelector(".lightbox-flecha.siguiente");
    const contenedorPrincipal = document.querySelector(".contenedor-premios");

    // Variables de control para la navegación interna
    let imagenesGaleriaActual = [];
    let indiceActual = 0;

    if (modal && imgModal && contenedorPrincipal) {
        
        // Al hacer clic en una miniatura
        contenedorPrincipal.addEventListener("click", (evento) => {
            const miniatura = evento.target.closest(".galeria-tarjeta img");
            if (!miniatura) return;

            // Buscamos la galería específica de la tarjeta donde se hizo clic
            const galeriaContenedor = miniatura.closest(".galeria-tarjeta");
            // Guardamos todas las fotos de esa tarjeta en un array (lista)
            imagenesGaleriaActual = Array.from(galeriaContenedor.querySelectorAll("img"));
            // Buscamos la posición numérica de la foto cliqueada dentro de esa lista
            indiceActual = imagenesGaleriaActual.indexOf(miniatura);

            actualizarImagenModal();
            
            modal.classList.add("activo");
            document.body.style.overflow = "hidden";
        });

        // Función centralizada para renderizar la imagen en grande
        const actualizarImagenModal = () => {
            const fotoSeleccionada = imagenesGaleriaActual[indiceActual];
            if (!fotoSeleccionada) return;
            
            imgModal.src = fotoSeleccionada.src;
            imgModal.alt = fotoSeleccionada.alt;
        };

        // Avanzar a la siguiente foto de la sección
        const siguienteImagen = () => {
            if (imagenesGaleriaActual.length === 0) return;
            // Si llega al final de las fotos, vuelve a empezar desde la primera (bucle continuo)
            indiceActual = (indiceActual + 1) % imagenesGaleriaActual.length;
            actualizarImagenModal();
        };

        // Retroceder a la foto anterior de la sección
        const anteriorImagen = () => {
            if (imagenesGaleriaActual.length === 0) return;
            // Si está en la primera y va hacia atrás, salta a la última foto
            indiceActual = (indiceActual - 1 + imagenesGaleriaActual.length) % imagenesGaleriaActual.length;
            actualizarImagenModal();
        };

        // Cierre limpio del modal
        const cerrarLightbox = () => {
            modal.classList.remove("activo");
            document.body.style.overflow = "";
            setTimeout(() => { imgModal.src = ""; imagenesGaleriaActual = []; }, 300); 
        };

        // Asignación de clics en los botones de navegación
        flechaSig.addEventListener("click", (e) => { e.stopPropagation(); siguienteImagen(); });
        flechaAnt.addEventListener("click", (e) => { e.stopPropagation(); anteriorImagen(); });
        botonCerrar.addEventListener("click", cerrarLightbox);

        // Cerrar al tocar el fondo oscuro externo
        modal.addEventListener("click", (evento) => {
            if (evento.target === modal) cerrarLightbox();
        });

        // Control por teclado avanzado (Muy cómodo en PC)
        document.addEventListener("keydown", (evento) => {
            if (!modal.classList.contains("activo")) return;
            
            if (evento.key === "ArrowRight") siguienteImagen(); // Flecha derecha del teclado
            if (evento.key === "ArrowLeft") anteriorImagen();   // Flecha izquierda del teclado
            if (evento.key === "Escape") cerrarLightbox();      // Tecla de Escape
        });
    }
});

document.addEventListener("DOMContentLoaded", () => {
    
    // ---------------------------------------------------------
    // 1. ANIMACIÓN DE ENTRADA SUAVE (SCROLL REVEAL)
    // ---------------------------------------------------------
    const tarjetas = document.querySelectorAll(".tarjeta-premio");
    const opcionesScroll = { root: null, rootMargin: "0px", threshold: 0.10 };

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
    // 2. CORRECCIÓN DEL LIGHTBOX CON NAVEGACIÓN POR FLECHAS
    // ---------------------------------------------------------
    const modal = document.getElementById("lightbox-modal");
    const imgModal = document.getElementById("lightbox-img");
    const botonCerrar = document.querySelector(".lightbox-cerrar");
    const flechaAnt = document.querySelector(".lightbox-flecha.anterior");
    const flechaSig = document.querySelector(".lightbox-flecha.siguiente");
    const contenedorPrincipal = document.querySelector(".contenedor-premios");

    let imagenesGaleriaActual = [];
    let indiceActual = 0;

    if (modal && imgModal && contenedorPrincipal) {
        
        // Delegación de eventos ultra-precisa para el carrusel horizontal
        contenedorPrincipal.addEventListener("click", (evento) => {
            // Buscamos si el clic ocurrió en una imagen que está dentro de una galería
            const miniatura = evento.target.closest(".galeria-tarjeta img");
            if (!miniatura) return; // Si no es una foto, ignoramos el clic

            // Encontramos el carrusel específico de esa tarjeta de premio
            const galeriaContenedor = miniatura.closest(".galeria-tarjeta");
            
            // Guardamos la lista de todas las fotos de esa sección en un array
            imagenesGaleriaActual = Array.from(galeriaContenedor.querySelectorAll("img"));
            
            // Identificamos el índice de la foto cliqueada
            indiceActual = imagenesGaleriaActual.indexOf(miniatura);

            // Cargamos la imagen grande y abrimos el Lightbox
            actualizarImagenModal();
            modal.classList.add("activo");
            document.body.style.overflow = "hidden"; // Bloquea el scroll de fondo
        });

        // Función para renderizar el diploma en grande
        const actualizarImagenModal = () => {
            if (imagenesGaleriaActual.length === 0) return;
            const fotoSeleccionada = imagenesGaleriaActual[indiceActual];
            
            imgModal.src = fotoSeleccionada.src;
            imgModal.alt = fotoSeleccionada.alt;
        };

        // Avanzar a la siguiente foto de la sección
        const siguienteImagen = () => {
            if (imagenesGaleriaActual.length === 0) return;
            indiceActual = (indiceActual + 1) % imagenesGaleriaActual.length;
            actualizarImagenModal();
        };

        // Retroceder a la foto anterior de la sección
        const anteriorImagen = () => {
            if (imagenesGaleriaActual.length === 0) return;
            indiceActual = (indiceActual - 1 + imagenesGaleriaActual.length) % imagenesGaleriaActual.length;
            actualizarImagenModal();
        };

        // Cierre limpio de la ventana flotante
        const cerrarLightbox = () => {
            modal.classList.remove("activo");
            document.body.style.overflow = ""; // Devuelve el scroll normal a la web
            setTimeout(() => { imgModal.src = ""; imagenesGaleriaActual = []; }, 250); 
        };

        // Eventos para los botones de las flechas y cierre
        flechaSig.addEventListener("click", (e) => { e.stopPropagation(); siguienteImagen(); });
        flechaAnt.addEventListener("click", (e) => { e.stopPropagation(); anteriorImagen(); });
        botonCerrar.addEventListener("click", cerrarLightbox);

        // Cerrar si se hace clic en la parte oscura exterior de la pantalla
        modal.addEventListener("click", (evento) => {
            if (evento.target === modal) cerrarLightbox();
        });

        // Soporte para teclado físico (Flechas e Izquierda/Derecha en PC)
        document.addEventListener("keydown", (evento) => {
            if (!modal.classList.contains("activo")) return;
            
            if (evento.key === "ArrowRight") siguienteImagen();
            if (evento.key === "ArrowLeft") anteriorImagen();
            if (evento.key === "Escape") cerrarLightbox();
        });
    }
});

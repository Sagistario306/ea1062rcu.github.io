document.addEventListener("DOMContentLoaded", () => {
    
    // ============================================
    // 1. REVELADO AL HACER SCROLL
    // ============================================
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

    // ============================================
    // 2. SISTEMA "MOSTRAR MÁS" IMÁGENES
    // ============================================
    const IMAGENES_INICIALES = 6;      // Cuántas imágenes mostrar al inicio
    const IMAGENES_POR_CARGA = 6;      // Cuántas añadir cada vez que se hace clic
    
    const galerias = document.querySelectorAll(".galeria-tarjeta");
    
    galerias.forEach((galeria, indice) => {
        const imagenes = galeria.querySelectorAll("img");
        const boton = document.querySelector(`.boton-mostrar-mas[data-galeria="${indice}"]`);
        
        if (!boton) return;
        
        // Si hay menos imágenes que el límite inicial, no mostrar el botón
        if (imagenes.length <= IMAGENES_INICIALES) {
            boton.style.display = "none";
            return;
        }
        
        // Ocultar imágenes que exceden el límite inicial
        imagenes.forEach((img, i) => {
            if (i >= IMAGENES_INICIALES) {
                img.classList.add("oculto");
            }
        });
        
        let imagenesVisibles = IMAGENES_INICIALES;
        
        // Evento del botón "Mostrar más"
        boton.addEventListener("click", () => {
            const nuevasVisibles = Math.min(imagenesVisibles + IMAGENES_POR_CARGA, imagenes.length);
            
            // Mostrar las nuevas imágenes
            for (let i = imagenesVisibles; i < nuevasVisibles; i++) {
                imagenes[i].classList.remove("oculto");
            }
            
            imagenesVisibles = nuevasVisibles;
            
            // Si ya se mostraron todas, ocultar el botón
            if (imagenesVisibles >= imagenes.length) {
                boton.style.display = "none";
            } else {
                // Actualizar el texto del botón con el contador
                const restantes = imagenes.length - imagenesVisibles;
                boton.textContent = `➕ Mostrar más imágenes (${restantes} restantes)`;
            }
        });
    });

    // ============================================
    // 3. CONTROL DEL LIGHTBOX INTEGRAL
    // ============================================
    const modal = document.getElementById("lightbox-modal");
    const imgModal = document.getElementById("lightbox-img");
    const botonCerrar = document.querySelector(".lightbox-cerrar");
    const flechaAnt = document.querySelector(".lightbox-flecha.anterior");
    const flechaSig = document.querySelector(".lightbox-flecha.siguiente");
    const contenedorPrincipal = document.querySelector(".contenedor-premios");

    let imagenesGaleriaActual = [];
    let indiceActual = 0;

    if (modal && imgModal && contenedorPrincipal) {
        
        contenedorPrincipal.addEventListener("click", (evento) => {
            const miniatura = evento.target.closest(".galeria-tarjeta img:not(.oculto)");
            if (!miniatura) return;

            const galeriaContenedor = miniatura.closest(".galeria-tarjeta");
            // Solo incluir imágenes visibles en el lightbox
            imagenesGaleriaActual = Array.from(galeriaContenedor.querySelectorAll("img:not(.oculto)"));
            indiceActual = imagenesGaleriaActual.indexOf(miniatura);

            actualizarImagenModal();
            modal.classList.add("activo");
            document.body.style.overflow = "hidden";
        });

        const actualizarImagenModal = () => {
            if (imagenesGaleriaActual.length === 0) return;
            const fotoSeleccionada = imagenesGaleriaActual[indiceActual];
            imgModal.src = fotoSeleccionada.getAttribute('src');
            imgModal.alt = fotoSeleccionada.alt || "Diploma EA1062RCU";
        };

        const siguienteImagen = () => {
            if (imagenesGaleriaActual.length === 0) return;
            indiceActual = (indiceActual + 1) % imagenesGaleriaActual.length;
            actualizarImagenModal();
        };

        const anteriorImagen = () => {
            if (imagenesGaleriaActual.length === 0) return;
            indiceActual = (indiceActual - 1 + imagenesGaleriaActual.length) % imagenesGaleriaActual.length;
            actualizarImagenModal();
        };

        const cerrarLightbox = () => {
            modal.classList.remove("activo");
            document.body.style.overflow = "";
            imgModal.src = ""; 
            imagenesGaleriaActual = [];
        };

        flechaSig.addEventListener("click", (e) => { e.stopPropagation(); siguienteImagen(); });
        flechaAnt.addEventListener("click", (e) => { e.stopPropagation(); anteriorImagen(); });
        botonCerrar.addEventListener("click", cerrarLightbox);
        modal.addEventListener("click", (evento) => { if (evento.target === modal) cerrarLightbox(); });

        document.addEventListener("keydown", (evento) => {
            if (!modal.classList.contains("activo")) return;
            if (evento.key === "ArrowRight") siguienteImagen();
            if (evento.key === "ArrowLeft") anteriorImagen();
            if (evento.key === "Escape") cerrarLightbox();
        });
    }
});

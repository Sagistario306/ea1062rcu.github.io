document.addEventListener("DOMContentLoaded", () => {
    
    // 1. REVELADO AL HACER SCROLL
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

    // 2. CONTROL DEL LIGHTBOX INTEGRAL
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
            const miniatura = evento.target.closest(".galeria-tarjeta img");
            if (!miniatura) return;

            const galeriaContenedor = miniatura.closest(".galeria-tarjeta");
            imagenesGaleriaActual = Array.from(galeriaContenedor.querySelectorAll("img"));
            indiceActual = imagenesGaleriaActual.indexOf(miniatura);

            actualizarImagenModal();
            modal.classList.add("activo");
            document.body.style.overflow = "hidden";
        });

        const actualizarImagenModal = () => {
            if (imagenesGaleriaActual.length === 0) return;
            const fotoSeleccionada = imagenesGaleriaActual[indiceActual];
            
            // Corrección de Ruta Absoluta para evitar el fallo de imagen rota
            const rutaLimpia = fotoSeleccionada.getAttribute('src');
            imgModal.src = rutaLimpia;
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

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
    // 2. CONTROL DEL LIGHTBOX CON NAVEGACIÓN EN SERIE (CORREGIDO)
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
        
        // Delegación de eventos precisa para capturar clics en las miniaturas
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

        // FUNCIÓN CORREGIDA: Extrae y limpia la propiedad src nativa para evitar enlaces rotos
        const actualizarImagenModal = () => {
            if (imagenesGaleriaActual.length === 0) return;
            const fotoSeleccionada = imagenesGaleriaActual[indiceActual];
            
            if (fotoSeleccionada) {
                // Usamos el atributo exacto del DOM para que GitHub resuelva la ruta real de la foto
                imgModal.setAttribute("src", fotoSeleccionada.getAttribute("src"));
                imgModal.setAttribute("alt", fotoSeleccionada.getAttribute("alt") || "Diploma EA1062RCU");
            }
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
            document.body.style.overflow = ""; 
            setTimeout(() => { imgModal.src = ""; imagenesGaleriaActual = []; }, 200); 
        };

        // Eventos para los controles
        flechaSig.addEventListener("click", (e) => { e.stopPropagation(); siguienteImagen(); });
        flechaAnt.addEventListener("click", (e) => { e.stopPropagation(); anteriorImagen(); });
        botonCerrar.addEventListener("click", cerrarLightbox);

        modal.addEventListener("click", (evento) => {
            if (evento.target === modal) cerrarLightbox();
        });

        document.addEventListener("keydown", (evento) => {
            if (!modal.classList.contains("activo")) return;
            if (evento.key === "ArrowRight") siguienteImagen();
            if (evento.key === "ArrowLeft") anteriorImagen();
            if (evento.key === "Escape") cerrarLightbox();
        });
    }

    // ---------------------------------------------------------
    // 3. RELOJ UTC DINÁMICO EN TIEMPO REAL
    // ---------------------------------------------------------
    const actualizarRelojUTC = () => {
        const elementoReloj = document.getElementById("reloj-utc");
        if (!elementoReloj) return;

        const ahora = new Date();
        const horas = String(ahora.getUTCHours()).padStart(2, '0');
        const minutos = String(ahora.getUTCMinutes()).padStart(2, '0');
        const segundos = String(ahora.getUTCSeconds()).padStart(2, '0');

        elementoReloj.textContent = `${horas}:${minutos}:${segundos} UTC`;
    };

    actualizarRelojUTC();
    setInterval(actualizarRelojUTC, 1000);
});

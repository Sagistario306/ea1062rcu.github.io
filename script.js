document.addEventListener("DOMContentLoaded", () => {
    // Seleccionamos todas las tarjetas de premios
    const tarjetas = document.querySelectorAll(".tarjeta-premio");
    
    // Configuración del detector de movimiento (Scroll)
    const opciones = {
        root: null,          // Usa la pantalla del navegador como referencia
        rootMargin: "0px",   // Sin márgenes extra
        threshold: 0.15      // La animación se activa cuando se ve el 15% de la tarjeta
    };

    // Función que añade la clase visible cuando la tarjeta entra en pantalla
    const aparecerAlHacerScroll = new IntersectionObserver((entradas, observador) => {
        entradas.forEach(entrada => {
            if (entrada.isIntersecting) {
                // Añade la clase que activa la animación CSS
                entrada.target.classList.add("tarjeta-visible");
                // Deja de observar la tarjeta para ahorrar memoria RAM
                observador.unobserve(entrada.target);
            }
        });
    }, opciones);

    // Activamos el observador en cada una de las tarjetas
    tarjetas.forEach(tarjeta => {
        aparecerAlHacerScroll.observe(tarjeta);
    });
});

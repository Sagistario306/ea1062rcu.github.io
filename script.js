document.addEventListener("DOMContentLoaded", () => {
    const contenedor = document.querySelector(".contenedor-premios");
    
    if (contenedor) {
        console.log("Estructura de cuadrícula de EA1062RCU inicializada correctamente.");
        
        // Ejemplo: Si en el futuro necesitas añadir una clase activa mediante JS
        const tarjetas = contenedor.querySelectorAll(".tarjeta-premio");
        tarjetas.forEach(tarjeta => {
            tarjeta.addEventListener("click", () => {
                // Remueve la selección de otras tarjetas si es necesario
                tarjetas.forEach(t => t.classList.remove("seleccionada"));
                // Añade la clase a la tarjeta clickeada
                tarjeta.classList.add("seleccionada");
            });
        });
    } else {
        console.warn("No se encontró el contenedor .contenedor-premios en el DOM.");
    }
});

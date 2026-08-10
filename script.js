// Esperar a que el diseño cargue por completo
document.addEventListener("DOMContentLoaded", () => {
    const tarjetas = document.querySelectorAll(".premio-card");

    // Añadir efecto de interacción con JavaScript al hacer clic
    tarjetas.forEach(tarjeta => {
        tarjeta.addEventListener("click", () => {
            // Quitamos el efecto a cualquier otra tarjeta primero
            tarjetas.forEach(t => t.style.borderColor = "#e1e4e8");
            
            // Resaltamos la tarjeta seleccionada cambiando el borde a dorado
            tarjeta.style.borderColor = "#d4af37";
            tarjeta.style.transition = "all 0.3s ease";
        });
    });
});

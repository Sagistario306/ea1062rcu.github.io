document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll('.award-card');

    cards.forEach(card => {
        card.addEventListener('click', () => {
            // Elimina el resalte de otras tarjetas
            cards.forEach(c => c.style.border = "none");
            // Añade resalte a la tarjeta seleccionada
            card.style.border = "2px solid #d4af37";
        });
    });
});

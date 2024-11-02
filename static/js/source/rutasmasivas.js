document.addEventListener("DOMContentLoaded", function() {
    // Ocultar los mensajes flash después de 5 segundos
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.classList.remove('show');
                message.classList.add('fade');
                setTimeout(() => message.remove(), 150);
            });
        }, 3000);
    }    
});
document.addEventListener("DOMContentLoaded", function() {
    // Ocultar los mensajes flash después de 3 segundos
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.classList.remove('show');
                message.classList.add('fade');
                setTimeout(() => message.remove(), 150); // Remover del DOM después de que se desvanezca
            });
        }, 3000); // 3000 ms = 3 segundos
    }

    //Script para mostrar/ocultar contraseñaks
    function setupPasswordToggle(toggleId, fieldId) {
        const toggle = document.getElementById(toggleId);
        const field = document.getElementById(fieldId);

        if (toggle && field) {
            // Mostrar la contraseña mientras se mantiene presionado el botón
            toggle.addEventListener("mousedown", function (e) {
                e.preventDefault(); // Prevenir comportamiento predeterminado
                field.setAttribute("type", "text");

                // Cambiar ícono a ojo abierto
                const eyeIcon = this.querySelector("i");
                if (eyeIcon) {
                    eyeIcon.classList.remove('fa-eye-slash');
                    eyeIcon.classList.add('fa-eye');
                }
            });

            // Ocultar la contraseña al soltar el botón
            toggle.addEventListener("mouseup", function (e) {
                e.preventDefault();
                field.setAttribute("type", "password");

                // Cambiar ícono a ojo cerrado
                const eyeIcon = this.querySelector("i");
                if (eyeIcon) {
                    eyeIcon.classList.remove('fa-eye');
                    eyeIcon.classList.add('fa-eye-slash');
                }
            });

            // Asegurar que la contraseña se oculte si el usuario sale del botón sin soltar (drag out)
            toggle.addEventListener("mouseleave", function () {
                field.setAttribute("type", "password");

                const eyeIcon = this.querySelector("i");
                if (eyeIcon) {
                    eyeIcon.classList.remove('fa-eye');
                    eyeIcon.classList.add('fa-eye-slash');
                }
            });
        } else {
            console.error(`No se encontró el toggle (${toggleId}) o el campo (${fieldId})`);
        }
    }

    // Configurar los toggles para los campos de contraseña
    setupPasswordToggle("togglePassword", "password");
});
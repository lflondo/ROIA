document.addEventListener("DOMContentLoaded", function () {
  // Variables globales
  const modal = new bootstrap.Modal(
    document.getElementById("startLocationModal")
  );
  const optimizeBtn = document.getElementById("optimizeRouteBtn");
  const confirmBtn = document.getElementById("confirmStartLocationBtn");
  const locationInput = document.getElementById("startLocationInput");

  // Modal de ID de ruta
  const rutaIdModal = new bootstrap.Modal(
    document.getElementById("rutaIdModal")
  );
  const verRutaOptimizadaBtn = document.getElementById("verRutaOptimizada");
  const buscarRutaBtn = document.getElementById("buscarRutaBtn");
  const rutaIdInput = document.getElementById("rutaIdInput");

  // Obtener el token CSRF del meta tag
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");

  // Función para validar el formato de la dirección
  function validateAddress(address) {
    // Dividir la dirección en partes
    const parts = address.split(",").map((part) => part.trim());

    // Verificar que haya al menos 3 partes (dirección, ciudad, país)
    if (parts.length < 3) {
      return {
        isValid: false,
        error:
          "La dirección debe incluir: dirección específica, ciudad y país (separados por comas)",
      };
    }

    // Verificar que ninguna parte esté vacía
    if (parts.some((part) => part.length === 0)) {
      return {
        isValid: false,
        error: "Todos los campos (dirección, ciudad y país) son obligatorios",
      };
    }

    // Verificar que la dirección tenga un número
    if (!/\d/.test(parts[0])) {
      return {
        isValid: false,
        error: "La dirección debe incluir un número",
      };
    }

    return {
      isValid: true,
      formattedAddress: parts.join(", "),
    };
  }

  // Mostrar mensajes de error en el modal
  function showError(message) {
    clearErrors(); // Limpiar errores anteriores
    const alertDiv = document.createElement("div");
    alertDiv.className = "alert alert-danger alert-dismissible fade show mt-3";
    alertDiv.innerHTML = `${message} <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    document.querySelector(".modal-body").appendChild(alertDiv);
  }

  // Limpiar mensajes de error
  function clearErrors() {
    document
      .querySelectorAll(".modal-body .alert")
      .forEach((alert) => alert.remove());
  }

  // Abrir el modal cuando se hace clic en "Optimizar Ruta"
  optimizeBtn.addEventListener("click", function () {
    clearErrors();
    locationInput.value = "";
    modal.show();
  });

  // Confirmar ubicación y enviar solicitud
  confirmBtn.addEventListener("click", async function () {
    const address = locationInput.value.trim();
    clearErrors();

    const validation = validateAddress(address);
    if (!validation.isValid) {
      showError(validation.error);
      return;
    }

    // Deshabilitar botón y mostrar loading
    try {
      confirmBtn.disabled = true;
      confirmBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...`;

      // Realizar la petición
      const response = await fetch("/optimizar_rutas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
          Accept: "application/json",
        },
        body: JSON.stringify({
          start_location: validation.formattedAddress,
          skip_geocoding: false,
        }),
      });

      // Manejar la respuesta
      if (!response.ok) {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Error al procesar la solicitud");
        } else {
          throw new Error("Error en el servidor");
        }
      }

      const data = await response.json();

      // Verificar si hay redirección
      if (data.redirect) {
        window.location.href = data.redirect;
      } else {
        throw new Error("No se recibió una redirección válida");
      }
    } catch (error) {
      console.error("Error:", error);
      showError(error.message || "Error al optimizar las rutas");
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = '<i class="fas fa-check me-2"></i>Confirmar';
    }

    // Enviar formulario al presionar "Enter" en el input de ubicación
    locationInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        confirmBtn.click();
      }
    });
  });
  // Limpiar el input y los errores cuando se cierra el modal
  document
    .getElementById("startLocationModal")
    .addEventListener("hidden.bs.modal", function () {
      clearErrors();
      locationInput.value = "";
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = '<i class="fas fa-check me-2"></i>Confirmar';
    });

  // Mostrar mensajes flash temporalmente
  const flashMessages = document.querySelectorAll(".alert");
  if (flashMessages) {
    setTimeout(function () {
      flashMessages.forEach((message) => {
        message.classList.remove("show");
        message.classList.add("fade");
        setTimeout(() => message.remove(), 150);
      });
    }, 3000);
  }

  // Autocompletado de barrios
  const barrioInput = document.getElementById("barrioInput");
  barrioInput.addEventListener("input", function () {
    const query = this.value.trim(); // Limpiamos el input
    const sugerencias = document.getElementById("sugerenciasBarrios");

    if (query.length < 2) {
      sugerencias.innerHTML = ""; // Limpiamos si la consulta es corta
      return;
    }

    fetch(`/buscar_barrio?q=${query}`)
      .then((response) => {
        if (!response.ok) throw new Error("Error en la respuesta del servidor");
        return response.json();
      })
      .then((data) => {
        sugerencias.innerHTML = "";
        if (Array.isArray(data) && data.length > 0) {
          data.forEach((barrio) => {
            const item = document.createElement("a");
            item.classList.add("list-group-item", "list-group-item-action");
            item.textContent = barrio;
            item.addEventListener("click", function () {
              barrioInput.value = barrio;
              sugerencias.innerHTML = "";
            });
            sugerencias.appendChild(item);
          });
        } else {
          console.log("No se encontraron coincidencias");
        }
      })
      .catch((error) => console.error("Error al buscar barrios:", error));
  });

  // Validación del formulario al enviar
  document.querySelector("form").addEventListener("submit", function (event) {
    barrioInput.value = barrioInput.value.trim();

    if (barrioInput.dataset.seleccionado !== "true") {
      fetch(`/buscar_barrio?q=${barrioInput.value}`)
        .then((response) => response.json())
        .then((data) => {
          if (!data.includes(barrioInput.value)) {
            event.preventDefault();
            alert(
              "El barrio ingresado no es válido. Por favor, intenta nuevamente."
            );
          } else {
            barrioInput.dataset.seleccionado = "true";
            this.submit();
          }
        })
        .catch((error) => {
          console.error("Error al verificar el barrio:", error);
          event.preventDefault();
        });
      event.preventDefault();
    }
  });

  // Resetear el estado de selección cuando el usuario modifica manualmente el input
  barrioInput.addEventListener("input", function () {
    this.dataset.seleccionado = "false";
  });

  const nuevaRutaLink = document.querySelector('a[href*="nueva_ruta"]');
  if (nuevaRutaLink) {
    nuevaRutaLink.addEventListener("click", function (e) {
      e.preventDefault();

      if (
        confirm(
          "¿Está seguro que desea crear una nueva ruta? Se eliminarán todos los registros actuales."
        )
      ) {
        window.location.href = this.href;
      }
    });
  }

  // Abrir modal al hacer clic en "Ver Ruta Optimizada"
  verRutaOptimizadaBtn.addEventListener("click", function (e) {
    e.preventDefault();
    rutaIdInput.value = "";
    rutaIdInput.classList.remove("is-invalid");
    rutaIdModal.show();
  });

  // Manejar la búsqueda de ruta
  buscarRutaBtn.addEventListener("click", async function () {
    const rutaId = rutaIdInput.value.trim();

    if (!rutaId) {
      rutaIdInput.classList.add("is-invalid");
      return;
    }

    try {
      buscarRutaBtn.disabled = true;
      buscarRutaBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Buscando...';

      const response = await fetch(`/verificar_ruta/${rutaId}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        // Si el contenido no es JSON, lanza un error personalizado
        const text = await response.text();
        throw new Error(`Error en la respuesta: ${text}`);
      }

      const data = await response.json();
      if (data.exists) {
        window.location.href = `/rutas_optimizadas/${rutaId}`;
      } else {
        throw new Error("Ruta no encontrada");
      }
    } catch (error) {
      console.log("Error detectado:", error);
      rutaIdInput.classList.add("is-invalid");
      document.querySelector(".invalid-feedback").textContent = error.message;
    } finally {
      buscarRutaBtn.disabled = false;
      buscarRutaBtn.innerHTML = '<i class="fas fa-search me-2"></i>Buscar';
    }
  });

  // Manejar entrada con Enter
  rutaIdInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      buscarRutaBtn.click();
    }
  });

  // Limpiar errores al cerrar el modal
  document
    .getElementById("rutaIdModal")
    .addEventListener("hidden.bs.modal", function () {
      rutaIdInput.classList.remove("is-invalid");
      rutaIdInput.value = "";
      buscarRutaBtn.disabled = false;
      buscarRutaBtn.innerHTML = '<i class="fas fa-search me-2"></i>Buscar';
    });
});

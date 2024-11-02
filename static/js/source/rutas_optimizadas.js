document.addEventListener("DOMContentLoaded", function() {
    const map = L.map('map').setView([6.2442, -75.5812], 12); // Centrado en Medellín
    

    // Añadir la capa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Recuperar los datos del contexto global
    const mapaRuta = window.appData.mapaRuta;
    const pedidos = window.appData.pedidos;
    const startLocation = window.appData.startLocation;

    console.log('Datos de la ruta:', {
        mapaRuta: mapaRuta,
        pedidos: pedidos,
        startLocation: startLocation
    });
    

    if (mapaRuta && mapaRuta.legs && mapaRuta.legs.length > 0) {
         // Crear array de coordenadas comenzando con el punto de inicio
        let coordinates = []
        let markers = []

        coordinates.push([startLocation.lat, startLocation.lng]); // Punto de inicio


         // Agregar marcador para el punto de inicio
         markers.push(L.marker([startLocation.lat, startLocation.lng])
         .addTo(map)
         .bindPopup('Punto de Inicio')
         .setIcon(L.icon({
             iconUrl: '/static/img/start-marker.png',
             iconSize: [25, 41],
             iconAnchor: [12, 41],
             popupAnchor: [1, -34]
         })));

        pedidos.forEach((pedido, index) => {
            let location;
            
            // Para el primer pedido, usar start_location del primer leg
            if (index === 0) {
                location = mapaRuta.legs[0].start_location;
            }
            // Para el último pedido, usar end_location del último leg
            else if (index === pedidos.length - 1) {
                location = mapaRuta.legs[mapaRuta.legs.length - 1].end_location;
            }
            // Para los pedidos intermedios, usar start_location del siguiente leg
            else {
                location = mapaRuta.legs[index].start_location;
            }

            if (location) {
                coordinates.push([location.lat, location.lng]);
            
                // Crear contenido detallado para el popup
                const markerContent = `
                    <strong>Pedido ${index + 1}</strong><br>
                    <strong>Cliente:</strong> ${pedido.nombre_cliente}<br>
                    <strong>Dirección:</strong> ${pedido.direccion}<br>
                    <strong>Barrio:</strong> ${pedido.barrio}<br>
                    <strong>Ciudad:</strong> ${pedido.ciudad}
                `;

                // Crear y agregar el marcador
                const marker = L.marker([location.lat, location.lng])
                    .addTo(map)
                    .bindPopup(markerContent);

                markers.push(marker);

                // Log para debugging
                console.log(`Pedido ${index + 1}:`, {
                    cliente: pedido.nombre_cliente,
                    barrio: pedido.barrio,
                    coordenadas: [location.lat, location.lng]
                });
            }else{
                console.error(`No se pudo obtener la ubicación del pedido ${index + 1}`);
            };   
        });
        
           
        // Crear la polyline y añadirla al mapa
        const polyline = L.polyline(coordinates, {
             color: 'red', 
             weight: 3, 
             opacity: 0.7 
            }).addTo(map);

        // Crear un grupo de capas con todos los marcadores y la polyline
        const group = L.featureGroup([...markers, polyline]);

        // Ajustar el zoom para mostrar toda la ruta
        map.fitBounds(group.getBounds(), { 
            padding: [50, 50] 
        });
        // Agregar logs adicionales para verificación
        console.log('Coordenadas finales:', coordinates);
        console.log('Número total de marcadores:', markers.length);

    } else {
        console.error('No se pudo cargar la ruta optimizada');
        alert("No se pudo cargar la ruta optimizada.");
    }

    // // Función para calcular totales
    // function calculateTotals(mapaRuta) {
    //     let totalTimeSeconds = 0;
    //     let totalDistanceMeters = 0;

    //     if (mapaRuta && mapaRuta.legs) {
    //         mapaRuta.legs.forEach(leg => {
    //             if (leg.duration && leg.duration.value) {
    //                 totalTimeSeconds += leg.duration.value;
    //             }
    //             if (leg.distance && leg.distance.value) {
    //                 totalDistanceMeters += leg.distance.value;
    //             }
    //         });
    //     }

    //     // Formatear tiempo
    //     const hours = Math.floor(totalTimeSeconds / 3600);
    //     const minutes = Math.floor((totalTimeSeconds % 3600) / 60);
    //     const timeString = hours > 0 
    //         ? `${hours} h ${minutes} min`
    //         : `${minutes} min`;

    //     // Formatear distancia
    //     const distanceString = totalDistanceMeters >= 1000
    //         ? `${(totalDistanceMeters / 1000).toFixed(1)} km`
    //         : `${Math.round(totalDistanceMeters)} m`;

    //     // Actualizar elementos en el DOM
    //     document.getElementById('totalTime').textContent = timeString;
    //     document.getElementById('totalDistance').textContent = distanceString;

    //     // Guardar los totales para referencia
    //     return {
    //         totalTime: timeString,
    //         totalDistance: distanceString
    //     };
    // }

    // // Calcular y mostrar totales
    // const routeTotals = calculateTotals(mapaRuta);


    // Añadir animación suave al colapsar/expandir
    const routeList = document.getElementById('routeList');
    routeList.addEventListener('show.bs.collapse', function () {
        this.style.transition = 'all 0.3s ease';
    });
    routeList.addEventListener('hide.bs.collapse', function () {
        this.style.transition = 'all 0.3s ease';
    });
});
import aiohttp
import asyncio
import logging

class AsyncGoogleMapsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        logging.info(f"GoogleMapsAPI initialized with key: {api_key[:5]}...")  # Log solo los primeros 5 caracteres por seguridad

    async def fetch(self, url, params):
        """Realiza una solicitud asíncrona al URL proporcionado con los parámetros."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def geocode(self, address):
        """Convierte una dirección en coordenadas (latitud y longitud) utilizando la API de Google Maps."""
        try:
            params = {'address': address, 'key': self.api_key}
            data = await self.fetch(self.geocode_url, params)
            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']
            else:
                logging.error(f"Error en Google Maps Geocoding API: {data['status']}")
                return None, None
        except Exception as e:
            logging.error(f"Error geocodificando la dirección {address}: {str(e)}")
            return None, None

    async def get_travel_time(self, origin, destination):
        """Obtiene el tiempo estimado de viaje entre dos ubicaciones."""
        try:
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "key": self.api_key,
                "departure_time": "now",
                "traffic_model": "best_guess"
            }
            data = await self.fetch(self.base_url, params)
            if data['status'] == 'OK':
                return data['routes'][0]['legs'][0]['duration_in_traffic']['value']
            else:
                logging.error(f"Error en Google Maps API: {data['status']}")
                return None
        except Exception as e:
            logging.error(f"Error obteniendo el tiempo de viaje: {str(e)}")
            return None

    async def get_route_data(self, origin, destination, waypoints):
        """Obtiene la ruta optimizada con Google Maps Directions API."""
        try:
            waypoints_str = "|".join([f"{wp[0]},{wp[1]}" for wp in waypoints])
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "waypoints": waypoints_str,
                "optimize": "true",
                "key": self.api_key,
                "departure_time": "now",
                "traffic_model": "best_guess"
            }
            data = await self.fetch(self.base_url, params)
            if data['status'] == 'OK':
                return data['routes'][0]['legs'], data['routes'][0]
            else:
                logging.error(f"Error en Google Maps API: {data['status']}")
                return None, None
        except Exception as e:
            logging.error(f"Error obteniendo datos de ruta: {str(e)}")
            return None, None

    async def get_distance(self, origin, destination):
        """Obtiene la distancia entre dos puntos usando la API de Distance Matrix de Google Maps."""
        try:
            params = {
                "origins": f"{origin[0]},{origin[1]}",
                "destinations": f"{destination[0]},{destination[1]}",
                "key": self.api_key,
                "mode": "driving"
            }
            data = await self.fetch(self.distance_matrix_url, params)
            if data['status'] == 'OK':
                distance = data['rows'][0]['elements'][0]['distance']['value']  # Distancia en metros
                return distance
            else:
                logging.error(f"Error en Distance Matrix API: {data['status']}")
                return None
        except Exception as e:
            logging.error(f"Error obteniendo distancia: {str(e)}")
            return None

from typing import Dict, Union, Tuple
import logging
from services.api_google_maps import AsyncGoogleMapsAPI # Asegúrate de tener este import correcto

class GeocodingHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.google_maps_api = AsyncGoogleMapsAPI(api_key)
        
        # Coordenadas por defecto para diferentes ciudades/regiones
        self.default_coordinates = {
            'medellin': {'lat': 6.2442, 'lng': -75.5812},
            'bogota': {'lat': 4.7110, 'lng': -74.0721},
            'cali': {'lat': 3.4516, 'lng': -76.5320},
            # Agregar más ciudades según sea necesario
        }
    
    async def get_coordinates(self, address: str, city: str = None) -> Dict[str, float]:
        try:
            # Primer intento: geocodificación normal
            coords = await self.google_maps_api.geocode(address)
            if coords and self._are_valid_coordinates(coords):
                return coords
            
            # Segundo intento: usar el nombre de la ciudad/región
            if city:
                city_coords = await self.google_maps_api.geocode(city)
                if self._are_valid_coordinates(city_coords):
                    logging.info(f"Usando coordenadas de la ciudad {city} como fallback")
                    return city_coords
            
            # Último recurso: usar coordenadas por defecto
            return self._get_default_coordinates(city)
            
        except Exception as e:
            logging.error(f"Error en geocodificación para {address}: {str(e)}")
            return self._get_default_coordinates(city)
    
    def _are_valid_coordinates(self, coords: Union[Dict[str, float], Tuple[float, float]]) -> bool:
        if isinstance(coords, dict):
            return 'lat' in coords and 'lng' in coords
        elif isinstance(coords, tuple) and len(coords) == 2:
            return True
        return False
    
    def _get_default_coordinates(self, city: str = None) -> Dict[str, float]:
        if city and city.lower() in self.default_coordinates:
            return self.default_coordinates[city.lower()]
        # Si no se encuentra la ciudad, usar Medellín como default
        return self.default_coordinates['medellin']
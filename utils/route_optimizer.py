# route_optimizer.py
from performance_monitor import PerformanceMonitor
from flask import jsonify
import logging

class RouteOptimizer:
    def __init__(self, app):
        self.app = app
        self.performance_monitor = PerformanceMonitor()
        self.logger = logging.getLogger(__name__)
        
    @performance_monitor.measure_performance
    async def optimize_routes(self, data: dict) -> tuple:
        """
        Optimiza las rutas y retorna los resultados junto con métricas de rendimiento
        """
        try:
            # Validación de datos de entrada
            if not self._validate_input(data):
                raise ValueError("Datos de entrada inválidos")
                
            # Proceso de optimización existente
            start_location = data.get('start_location')
            optimizer = DijkstraClarkeWrightOptimizer(
                locations=self._get_locations(data),
                google_maps_api=self._initialize_maps_api()
            )
            
            # Calcular ruta optimizada
            optimized_route = await optimizer.optimize_route(start_location)
            
            return {
                'route': optimized_route,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Error en optimización de ruta: {str(e)}")
            raise
            
    def _validate_input(self, data: dict) -> bool:
        """Valida los datos de entrada"""
        required_fields = ['start_location']
        return all(field in data for field in required_fields)
        
    def _get_locations(self, data: dict) -> list:
        """Obtiene las ubicaciones del conjunto de datos"""
        # Implementa la lógica específica para obtener ubicaciones
        pass
        
    def _initialize_maps_api(self):
        """Inicializa la API de Google Maps"""
        # Implementa la inicialización de la API
        pass

# Modificación del endpoint Flask
@app.route('/optimizar_rutas', methods=['POST'])
async def optimizar_rutas():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    try:
        data = request.get_json()
        route_optimizer = RouteOptimizer(app)
        result, metrics = await route_optimizer.optimize_routes(data)
        
        # Agregar métricas al resultado
        response_data = {
            'route': result['route'],
            'metrics': {
                'execution_time': metrics.execution_time,
                'memory_usage': metrics.memory_usage,
                'peak_memory': metrics.peak_memory,
                'cpu_percent': metrics.cpu_percent
            },
            'redirect': url_for('mostrar_rutas_optimizadas')
        }
        
        return jsonify(response_data)
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
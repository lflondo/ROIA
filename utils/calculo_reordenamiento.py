import numpy as np
import asyncio
import aiohttp
import random
from heapq import heappop, heappush
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
from scipy.optimize import linear_sum_assignment
from functools import lru_cache
from aiocache import cached, Cache


class DijkstraClarkeWrightOptimizer:
    def __init__(self, locations, google_maps_api, threshold=float('inf'), savings_threshold=0):
        self.locations = locations
        self.num_locations = len(locations)
        self.google_maps_api = google_maps_api
        self.threshold = threshold
        self.savings_threshold = savings_threshold
        self.distance_matrix = np.zeros((self.num_locations, self.num_locations))
        self.time_matrix = np.zeros((self.num_locations, self.num_locations))
        self.scaler = MinMaxScaler()
        
    @cached(ttl=3600, cache=Cache.MEMORY)  # Ajusta el TTL como desees
    async def get_cached_distance_time(self, loc1, loc2):
        """Cachea y devuelve la distancia y el tiempo entre dos ubicaciones."""
        return await self.google_maps_api.get_distance(loc1, loc2), await self.google_maps_api.get_travel_time(loc1, loc2)

    async def calculate_matrices(self):
        """Calcula matrices de distancia y tiempo usando concurrencia y cache."""
        tasks = []
        for i in range(self.num_locations):
            for j in range(i + 1, self.num_locations):
                tasks.append(asyncio.create_task(
                    self.get_cached_distance_time(self.locations[i], self.locations[j])
                ))

        # Ejecuta las tareas en paralelo y actualiza las matrices
        results = await asyncio.gather(*tasks)
        idx = 0
        for i in range(self.num_locations):
            for j in range(i + 1, self.num_locations):
                distance, time = results[idx]
                idx += 1
                if distance is not None and time is not None:
                    self.distance_matrix[i][j] = self.distance_matrix[j][i] = distance
                    self.time_matrix[i][j] = self.time_matrix[j][i] = time
                else:
                    self.distance_matrix[i][j] = self.distance_matrix[j][i] = float('inf')
                    self.time_matrix[i][j] = self.time_matrix[j][i] = float('inf')

        # Ajusta el scaler para normalizar tiempos
        self.scaler.fit(self.time_matrix)
        self.normalized_time_matrix = self.scaler.transform(self.time_matrix)

    def dijkstra(self, start_node):
        """Implementa el algoritmo de Dijkstra para calcular las distancias más cortas desde start_node."""
        distances = {node: float('inf') for node in range(self.num_locations)}
        distances[start_node] = 0
        pq = [(0, start_node)]  # Priority queue, formato (distancia, nodo)

        while pq:
            current_distance, current_node = heappop(pq)

            if current_distance > distances[current_node]:
                continue

            for neighbor in range(self.num_locations):
                if neighbor == current_node:
                    continue
                distance = self.distance_matrix[current_node][neighbor]
                new_distance = current_distance + distance

                if new_distance < distances[neighbor] and new_distance <=self.threshold:
                    distances[neighbor] = new_distance
                    heappush(pq, (new_distance, neighbor))

        return distances

    def clarke_wright(self, depot, threshold=0):
        """Optimiza con Clarke-Wright, excluyendo ahorros bajos."""
        savings = []
        for i in range(self.num_locations):
            for j in range(i + 1, self.num_locations):
                if i != depot and j != depot:
                    cost_depot_i = self.distance_matrix[depot][i]
                    cost_depot_j = self.distance_matrix[depot][j]
                    cost_i_j = self.distance_matrix[i][j]
                    saving = cost_depot_i + cost_depot_j - cost_i_j
                    if saving > self.savings_threshold:  # Filtra ahorros bajos
                        savings.append((saving, i, j))

        savings.sort(reverse=True, key=lambda x: x[0])  # Ordenar por ahorro mayor

        routes = {i: [i] for i in range(self.num_locations) if i != depot}
        for saving, i, j in savings:
            if i in routes and j in routes:
                if len(routes[i]) + len(routes[j]) <= self.num_locations - 1:
                    routes[i].extend(routes[j])
                    del routes[j]

        best_route = [depot] + max(routes.values(), key=len)
        return best_route
    
    def tsp(self, start_index=0):
        """Implementa una solución para el Problema del Vendedor Viajero (TSP) minimizando la distancia total."""
        n = self.num_locations
        visited = [False] * n
        path = [start_index]
        visited[start_index] = True
        
        for _ in range(1, n):
            last = path[-1]
            nearest = None
            nearest_dist = float('inf')
            
            # Encontrar el nodo más cercano no visitado
            for j in range(n):
                if not visited[j] and self.distance_matrix[last][j] < nearest_dist:
                    nearest = j
                    nearest_dist = self.distance_matrix[last][j]
            
            if nearest is not None:  # Añadimos verificación
                path.append(nearest)
                visited[nearest] = True
            else:
                break  # Si no hay más nodos alcanzables, terminamos
            
        return path


    async def optimize_route(self, start_location):
        """Optimiza la ruta combinando Dijkstra para distancias y Clarke-Wright para tiempos."""
        if not self.locations:
            raise ValueError("No hay ubicaciones para optimizar")
            
        try:
            start_idx = self.locations.index(start_location)
        except ValueError:
            raise ValueError("La ubicación de inicio no se encuentra en la lista de ubicaciones")
        
        await self.calculate_matrices()
        distances_from_start = self.dijkstra(start_idx)
        best_route = self.tsp(start_idx)
        
        if not best_route or len(best_route) < 2:
            raise ValueError("No se pudo generar una ruta válida")
        
        return best_route
from flask import jsonify
from sqlalchemy import text
import json
import logging


class ModelRuta:
    
    @classmethod
    def get_all_rutas(cls, db):
        try:
            query = text( """
                SELECT rd.numero_pedido, rd.nombre_cliente, rd.direccion, rd.telefono,
                       b.descripcion AS barrio, c.descripcion AS ciudad,
                       d.descripcion AS departamento, p.descripcion AS pais
                FROM ruta_despacho rd
                JOIN egebarrio b ON rd.codigo_barrio = b.codigo
                JOIN egeciudad c ON rd.codigo_ciudad = c.codigo
                JOIN egedepartamento d ON rd.codigo_departamento = d.codigo
                JOIN egepais p ON rd.codigo_pais = p.codigo
            """)
            rutas = db.session.execute(query).mappings().all()
            return rutas
        except Exception as e:
            raise Exception(f"Error al obtener rutas: {e}")

    @classmethod
    def insert_ruta(cls, db, uuid, numero_pedido, nombre_cliente, direccion, telefono, barrio, ciudad, departamento, pais):
        try: 
            print(f"Insertando: {nombre_cliente}, {direccion}, {barrio}")  # Depuración

            # Obtener códigos para las descripciones dadas
            codes = cls._get_location_codes(db, barrio, ciudad, departamento, pais)
            
            query = text("""
                INSERT INTO ruta_despacho (uuid, numero_pedido, nombre_cliente, direccion, telefono, 
                                           codigo_barrio, codigo_ciudad, codigo_departamento, codigo_pais)
                VALUES (:uuid, :numero_pedido, :nombre_cliente, :direccion, :telefono, 
                        :codigo_barrio, :codigo_ciudad, :codigo_departamento, :codigo_pais)
            """)
            db.session.execute(query, {
                'uuid': uuid,
                'numero_pedido': numero_pedido,
                'nombre_cliente': nombre_cliente,
                'direccion': direccion,
                'telefono': telefono,
                'codigo_barrio': codes['barrio'],
                'codigo_ciudad': codes['ciudad'],
                'codigo_departamento': codes['departamento'],
                'codigo_pais': codes['pais']
            })
            db.session.commit()
            return True  # Retornar True si la inserción fue exitosa
        except ValueError as ve:
            db.session.rollback()
            print(f"Error en los datos de ubicación: {ve}")  # Depuración
            raise ValueError(f"Error en los datos de ubicación: {ve}")
        except Exception as e:
            db.session.rollback()
            print(f"Error al insertar ruta: {e}")  # Depuración
            raise Exception(f"Error al insertar ruta: {e}")

    @staticmethod
    def _get_location_codes(db, barrio, ciudad, departamento, pais):
        codes = {}
        
        # Definimos las tablas y los campos correspondientes
        locations = [
            ('barrio', 'egebarrio'), 
            ('ciudad', 'egeciudad'), 
            ('departamento', 'egedepartamento'), 
            ('pais', 'egepais')
        ]
        
        # Recorremos cada ubicación para obtener su código
        for location, table in locations:
            query = text(f"SELECT codigo FROM {table} WHERE UPPER(descripcion) = :descripcion")
            
            # Ejecutamos la consulta y obtenemos el primer resultado
            result = db.session.execute(query, {'descripcion': locals()[location].upper()}).fetchone()
            
            if result:
                codes[location] = result[0]
            else:
                raise ValueError(f"{location.capitalize()} no encontrado: {locals()[location]}")
        
        return codes
    
    @classmethod
    def pedido_existe(cls, db, numero_pedido):
        """Verifica si el número de pedido ya está registrado."""
        try:
            query = text("SELECT numero_pedido FROM ruta_despacho WHERE numero_pedido = :numero_pedido")
            pedido = db.session.execute(query, {'numero_pedido': numero_pedido}).fetchone()
            return pedido is not None  # Devuelve True si el pedido ya existe
        except Exception as e:
            raise Exception(f"Error al verificar si el pedido existe: {e}")
    
    @classmethod
    def buscar_barrio(cls, db, query):
        """Busca un barrio en la base de datos usando una consulta parcial."""
        try:
            # Convertimos el parámetro a mayúsculas y lo preparamos para la consulta
            query = query.strip().upper()
            print(f"Consulta enviada: {query}")  # Para depuración

            # Consulta SQL para buscar barrios similares
            sql = text("SELECT descripcion FROM egebarrio WHERE UPPER(descripcion) LIKE :query LIMIT 5")
            # Ejecutamos la consulta con el patrón '%<query>%'
            resultados = db.session.execute(sql, {'query': f"%{query}%"}).mappings().all()
            
            if not resultados:
                print("No se encontraron coincidencias")  # Log adicional
            else:
                print(f"Resultados: {[row['descripcion'] for row in resultados]}")

            # Extraemos los nombres de los barrios de los resultados
            return [row['descripcion'] for row in resultados]
        
        except Exception as e:
            print(f"Error al buscar barrio: {str(e)}")  # Log de errores
            raise Exception(f"Error al buscar barrio: {str(e)}")
    
    @classmethod
    def eliminar_ruta(cls, db, numero_pedido):
        """Elimina una ruta de la base de datos por su número de pedido."""
        try:
            query = text("DELETE FROM ruta_despacho WHERE numero_pedido = :numero_pedido")
            db.session.execute(query, {'numero_pedido': numero_pedido})
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar la ruta: {e}")
    
    @classmethod
    def obtener_ruta(cls, db, numero_pedido):
        """Obtiene los detalles de una ruta según el número de pedido."""
        try:
            query = text("""
                SELECT rd.numero_pedido, rd.nombre_cliente, rd.direccion, rd.telefono, 
                       b.descripcion AS barrio, c.descripcion AS ciudad, 
                       d.descripcion AS departamento, p.descripcion AS pais
                FROM ruta_despacho rd
                JOIN egebarrio b ON rd.codigo_barrio = b.codigo
                JOIN egeciudad c ON rd.codigo_ciudad = c.codigo
                JOIN egedepartamento d ON rd.codigo_departamento = d.codigo
                JOIN egepais p ON rd.codigo_pais = p.codigo
                WHERE rd.numero_pedido = :numero_pedido
            """)
            ruta = db.session.execute(query, {'numero_pedido': numero_pedido}).fetchone()
            #print(f"Resultado de la ruta: {ruta}")
            return ruta
        except Exception as e:
            raise Exception(f"Error al obtener la ruta: {e}")
        
        
    @classmethod
    def actualizar_ruta(cls, db, nuevo_numero_pedido, numero_pedido_actual, nombre_cliente, direccion, telefono, barrio, ciudad, departamento, pais):
        """Actualiza los detalles de una ruta, incluyendo el número de pedido."""
        try:
            # Obtener los códigos de ubicación
            codes = cls._get_location_codes(db, barrio, ciudad, departamento, pais)

            query = text("""UPDATE ruta_despacho 
                       SET numero_pedido = :nuevo_numero_pedido, nombre_cliente = :nombre_cliente, direccion = :direccion, telefono = :telefono,
                           codigo_barrio = :codigo_barrio, codigo_ciudad = :codigo_ciudad, codigo_departamento = :codigo_departamento, codigo_pais = :codigo_pais
                       WHERE numero_pedido = :numero_pedido_actual""")
            db.session.execute(query, {
                'nuevo_numero_pedido': nuevo_numero_pedido,
                'nombre_cliente': nombre_cliente,
                'direccion': direccion,
                'telefono': telefono,
                'codigo_barrio': codes['barrio'],
                'codigo_ciudad': codes['ciudad'],
                'codigo_departamento': codes['departamento'],
                'codigo_pais': codes['pais'],
                'numero_pedido_actual': numero_pedido_actual
            })
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al actualizar la ruta: {e}")
    
    @classmethod
    def clear_all_routes(cls, db):
        """Elimina todos los registros de la tabla ruta_despacho."""
        try:
            query = text("DELETE FROM ruta_despacho")
            db.session.execute(query)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al limpiar la tabla de rutas: {e}")
        
    

    @classmethod
    def insert_ruta_optimizada(cls, db, user_id, pedidos_optimizados, ruta_data, mapa_ruta, start_location):
        try:

           # Convertimos los objetos RowMapping a diccionarios
            pedidos_json = json.dumps([dict(pedido) for pedido in pedidos_optimizados])

            # Serializamos ruta_data y mapa_ruta de forma segura
            ruta_data_json = json.dumps(ruta_data if ruta_data else [])
            mapa_ruta_json = json.dumps(mapa_ruta if mapa_ruta else {})
            start_location_json = json.dumps(start_location if start_location else {})

            query = text("""
                INSERT INTO rutas_optimizadas (user_id, pedidos_optimizados, ruta_data, mapa_ruta, start_location, created_at)
                VALUES (:user_id, :pedidos_optimizados, :ruta_data, :mapa_ruta, :start_location, NOW())
            """)
            db.session.execute(query, {
                'user_id': user_id,
                'pedidos_optimizados': pedidos_json,
                'ruta_data': ruta_data_json,
                'mapa_ruta': mapa_ruta_json, 
                'start_location': start_location_json
            })
            db.session.commit()

            # Obtener el ID insertado
            inserted_id = db.session.execute(
                text("SELECT currval(pg_get_serial_sequence('rutas_optimizadas', 'id'))")
            ).scalar()
            logging.info(f"Ruta optimizada insertada con ID: {inserted_id}")
            return inserted_id
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al insertar ruta optimizada: {e}")
            raise Exception(f"Error al insertar ruta optimizada: {e}")

    
    @staticmethod
    def get_ruta_optimizada(db, ruta_optimizada_id):
        try:
            # Verifica si el parámetro ruta_optimizada_id tiene un valor válido
            if not ruta_optimizada_id:
                raise ValueError("El parámetro ruta_optimizada_id es nulo o vacío.")
            
            # Realiza la consulta con el id proporcionado
            query = text( """
                SELECT id, user_id, pedidos_optimizados, ruta_data, mapa_ruta, created_at, start_location
                FROM rutas_optimizadas
                WHERE id = :ruta_id
            """)

            result = db.session.execute(query, {"ruta_id": ruta_optimizada_id})
            # Recupera la primera fila del resultado
            ruta_optimizada = result.fetchone()
                
            # Devuelve los datos obtenidos
            if ruta_optimizada:
                return ruta_optimizada
                logging.info(f"Ruta optimizada encontrada: {ruta_optimizada}")
            else:
                raise Exception(f"No se encontró ninguna ruta con el id {ruta_optimizada_id}")
        
        except Exception as e:
            # Maneja y muestra el error
            raise Exception(f"Error al obtener ruta optimizada: {e}")
    
    
    @classmethod
    def verificar_ruta_optimizada(cls, db, ruta_id):
        """Verifica si existe una ruta optimizada con el ID dado."""
        try:
            query = text("""
                SELECT 1 
                FROM rutas_optimizadas 
                WHERE id = :ruta_id 
                LIMIT 1
            """)
            result = db.session.execute(query, {'ruta_id': ruta_id}).fetchone()
            return bool(result)
        except Exception as e:
            raise Exception(f"Error al verificar la ruta: {e}")

 

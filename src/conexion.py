import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración de conexión a la base de datos
DB_CONFIG = {
    "host": "",
    "database": "postgres",
    "user": "",
    "password": "",
}

def connect_to_db():

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("Error al conectar con la base de datos:", e)
        return None

#Registrar 
def register_data(table, data):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                values = tuple(data.values())
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                cursor.execute(query, values)
                conn.commit()
                print(f"Datos insertados correctamente en la tabla {table}.")
        except Exception as e:
            print(f"Error al insertar datos en la tabla {table}: {e}")
        finally:
            conn.close()

#Pedir Rol            
def get_user_role(username, password):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT rol FROM usuario WHERE nombre_usuario = %s AND clave = %s",
                    (username, password),
                )
                user = cursor.fetchone()
                return user["rol"] if user else None
        except Exception as e:
            print(f"Error al obtener rol del usuario: {e}")
            return None
        finally:
            conn.close()

#Consulta
def query_data(table, conditions=None, params=None): 
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Base de la consulta
                query = f"SELECT * FROM {table}"

                # Si hay condiciones, las agregamos
                if conditions:
                    query += f" WHERE {conditions}"

                # Ejecutamos la consulta con los parámetros proporcionados
                cursor.execute(query, params if params else ())
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"Error al consultar datos de la tabla {table}: {e}")
            return []
        finally:
            conn.close()

#Consulta personalizada
def execute_query(query, params=None):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params if params else ())
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"Error al ejecutar consulta: {e}")
            return []
        finally:
            conn.close()           

#Actualizacion
def update_data(table, updates, conditions, values):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                set_clause = ', '.join([f"{key} = %s" for key in updates.keys()])
                query = f"UPDATE {table} SET {set_clause} WHERE {conditions}"
                cursor.execute(query, values)  # Aquí pasa el `values` correctamente
                conn.commit()
                print(f"Datos actualizados correctamente en la tabla {table}.")
                return True  # Retornar True si se actualizó correctamente
        except Exception as e:
            print(f"Error al actualizar datos en la tabla {table}: {e}")
            return False
        finally:
            conn.close()

#Join Tables (consulta n tablas)
def join_tables(table1, table2, common_column, columns_to_select=None, conditions=None, params=None):

    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Determinar las columnas a seleccionar
                select_clause = ', '.join(columns_to_select) if columns_to_select else '*'
                
                # Construcción de la consulta sin alias
                query = f"""
                SELECT {select_clause}
                FROM {table1}  
                INNER JOIN {table2} ON {table1}.{common_column} = {table2}.{common_column} 
                """
                
                if conditions:
                    query += f" WHERE {conditions}"

                # Ejecutar la consulta pasando los parámetros como una tupla
                cursor.execute(query, params)  # Asegúrate de pasar los parámetros correctamente

                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"Error al realizar el JOIN entre {table1} y {table2}: {e}")
            return []
        finally:
            conn.close()

#Join_query
def query_with_joins(query, params=None):
    """
    Ejecuta una consulta con JOINs y devuelve los resultados.
    :param query: La consulta SQL con JOINs.
    :param params: Los parámetros de la consulta.
    :return: Resultados de la consulta.
    """
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Ejecutar la consulta
                cursor.execute(query, params if params else ())
                results = cursor.fetchall()
                # Convertir los resultados a un diccionario de tipo RealDictRow
                column_names = [desc[0] for desc in cursor.description]
                return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            print(f"Error al consultar datos: {e}")
            return []
        finally:
            conn.close()            

#Verificar existencias
def check_if_exists(query, params):
    """Verifica si existe un registro en la base de datos usando una consulta SQL."""
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()[0]  # Devolver el número de registros que coinciden con la condición
        conn.close()

        return result > 0  # Si existe al menos un registro, retornamos True
    except Exception as e:
        print(f"Error al verificar la existencia: {e}")
        return False
    
#Buscar
def buscar_datos(tabla, columna, valor):
    """
    Busca datos en una tabla de PostgreSQL con base en una columna y un valor.

    Args:
        tabla (str): Nombre de la tabla en la base de datos.
        columna (str): Nombre de la columna por la cual se realizará la búsqueda.
        valor (str): Valor que se usará como criterio de búsqueda.

    Returns:
        list: Lista de tuplas con los resultados de la búsqueda.
    """
    query = f"SELECT * FROM {tabla} WHERE {columna} ILIKE %s"
    conn = connect_to_db()
    if conn is None:
        print("No se pudo conectar a la base de datos.")
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (f"%{valor}%",))
            resultados = cursor.fetchall()
            return resultados
    except Exception as e:
        print(f"Error al buscar datos: {e}")
        return []
    finally:
        conn.close()

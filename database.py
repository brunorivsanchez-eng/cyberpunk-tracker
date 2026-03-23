import os
import psycopg
from psycopg import OperationalError
from psycopg.rows import dict_row
from dotenv import load_dotenv
from modelos import Personaje

# Carga de variables de entorno desde el archivo local .env
load_dotenv()

def conectar_bd():
    """Establece y retorna la conexión a NeonDB mapeando filas a diccionarios."""
    url_conexion = os.getenv("DATABASE_URL")
    if not url_conexion:
        print("Error Crítico: Variable DATABASE_URL no encontrada en el entorno.")
        return None

    try:
        return psycopg.connect(url_conexion, row_factory=dict_row)
    except OperationalError as e:
        print(f"Falla al conectar con la base de datos: {e}")
        return None

def cargar_partida_db():
    """Extrae el estado persistente de los jugadores desde PostgreSQL."""
    conexion = conectar_bd()
    if not conexion:
        return None, None

    pjs_cargados = []
    npcs_cargados = [] 

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM jugadores;")
            filas_jugadores = cursor.fetchall()

            for j in filas_jugadores:
                cursor.execute("""
                    SELECT pa.nombre, ij.balas_actuales, pa.max_balas,
                           COALESCE(string_agg(pr.descripcion, ' | '), '') as efecto
                    FROM inventario_jugadores ij
                    JOIN plantillas_armas pa ON ij.id_plantilla = pa.id_plantilla
                    LEFT JOIN armas_propiedades ap ON pa.id_plantilla = ap.id_plantilla
                    LEFT JOIN propiedades_armas pr ON ap.id_propiedad = pr.id_propiedad
                    WHERE ij.id_jugador = %s
                    GROUP BY pa.nombre, ij.balas_actuales, pa.max_balas;
                """, (j['id_jugador'],))
                
                dicc_armas = {
                    arma['nombre']: {
                        "actual": arma['balas_actuales'],
                        "max": arma['max_balas'],
                        "efecto": arma['efecto'] if arma['efecto'] else ""
                    } for arma in cursor.fetchall()
                }

                pj = Personaje(
                    nombre=j['nombre'], max_hp=j['max_hp'], max_body_sp=j['max_body_sp'],
                    max_head_sp=j['max_head_sp'], max_luck=j['max_luck'], move=j['max_move'],
                    armas=dicc_armas, death_penalty=j['death_penalty'], 
                    id_db=j['id_jugador'], es_npc=False
                )
                
                pj.hp = j['hp']
                pj.body_sp = j['body_sp']
                pj.head_sp = j['head_sp']
                pj.luck = j['luck']
                pj.move = j['move']
                
                cursor.execute("SELECT id_debufo FROM jugadores_debuffos WHERE id_jugador = %s;", (j['id_jugador'],))
                pj.debufos_permanentes_ids = [d['id_debufo'] for d in cursor.fetchall()]
                
                pjs_cargados.append(pj)

    except Exception as e:
        print(f"Error Crítico al ejecutar consultas SQL: {e}")
    finally:
        if conexion:
            conexion.close()

    return pjs_cargados, npcs_cargados

def guardar_partida_db(pjs, npcs):
    """Persiste el estado dinámico de los jugadores en la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        print("Error: Imposible establecer conexión. No se guardó la partida.")
        return

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_debufo FROM catalogo_debuffos WHERE nombre = '---';")
            ids_vacios = [row['id_debufo'] for row in cursor.fetchall()]

            for p in pjs:
                if getattr(p, 'id_db', None) is None:
                    continue
                
                cursor.execute("""
                    UPDATE jugadores 
                    SET hp = %s, body_sp = %s, head_sp = %s, luck = %s, move = %s, death_penalty = %s
                    WHERE id_jugador = %s;
                """, (p.hp, p.body_sp, p.head_sp, p.luck, p.move, p.death_penalty, p.id_db))

                if hasattr(p, "armas"):
                    for nombre_arma, datos in p.armas.items():
                        cursor.execute("""
                            UPDATE inventario_jugadores ij SET balas_actuales = %s
                            FROM plantillas_armas pa
                            WHERE ij.id_plantilla = pa.id_plantilla AND ij.id_jugador = %s AND pa.nombre = %s;
                        """, (datos["actual"], p.id_db, nombre_arma))

                cursor.execute("DELETE FROM jugadores_debuffos WHERE id_jugador = %s;", (p.id_db,))
                
                if hasattr(p, "debufos_permanentes_ids"):
                    for id_deb in set(p.debufos_permanentes_ids):
                        if id_deb not in ids_vacios:
                            cursor.execute("INSERT INTO jugadores_debuffos (id_jugador, id_debufo) VALUES (%s, %s);", (p.id_db, id_deb))
            
            conexion.commit()
            print("Estado general y de salud guardado exitosamente en NeonDB.")

    except Exception as e:
        conexion.rollback()
        print(f"Falla Crítica durante transacción DML (UPDATE): {e}")
    finally:
        if conexion:
            conexion.close()

def cargar_catalogos_debuffos():
    """Extrae los catálogos de estados alterados (Temporal y Permanente)."""
    conexion = conectar_bd()
    if not conexion:
        cat_vacio = [{"nombre": "---", "descripcion": "Sin conexión", "tipo": "Temporal"}]
        return cat_vacio, cat_vacio

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM catalogo_debuffos WHERE tipo = 'Temporal' ORDER BY id_debufo;")
            cat_temporales = cursor.fetchall()

            cursor.execute("SELECT * FROM catalogo_debuffos WHERE tipo = 'Permanente' ORDER BY id_debufo;")
            cat_permanentes = cursor.fetchall()
            
            return cat_temporales, cat_permanentes
    except Exception as e:
        print(f"Error Crítico al extraer catálogos de debuffos: {e}")
        return [], []
    finally:
        if conexion:
            conexion.close()

# --- database.py ---

def obtener_bestiario_completo():
    """Extrae todos los NPCs con sus metadatos para el Dialogo del Bestiario."""
    conn = conectar_bd()
    if not conn: return []
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id_npc, nombre, tier, faccion, max_hp, max_body_sp, max_head_sp, max_move 
            FROM npc 
            ORDER BY tier ASC, faccion ASC, nombre ASC
        """)
        
        bestiario = []
        for fila in cur.fetchall():
            # Validación robusta: extrae por nombre si es un diccionario (RealDictCursor), 
            # o por índice si es una tupla estándar.
            if isinstance(fila, dict) or hasattr(fila, 'keys'):
                bestiario.append({
                    "id": fila['id_npc'],
                    "nombre": fila['nombre'],
                    "tier": fila['tier'],
                    "faccion": fila['faccion'],
                    "hp": fila['max_hp'],
                    "body": fila['max_body_sp'],
                    "head": fila['max_head_sp'],
                    "move": fila['max_move']
                })
            else:
                bestiario.append({
                    "id": fila[0],
                    "nombre": fila[1],
                    "tier": fila[2],
                    "faccion": fila[3],
                    "hp": fila[4],
                    "body": fila[5],
                    "head": fila[6],
                    "move": fila[7]
                })
        return bestiario
    except Exception as e:
        # Se cambia a repr(e) para que, si ocurre otro error en el futuro, 
        # imprima el tipo de error exacto y no solo el valor.
        print(f"Error al obtener bestiario: {repr(e)}") 
        return []
    finally:
        conn.close()

def instanciar_npc_dinamico(id_npc):
    """Construye un objeto Personaje aislado en memoria basado en una plantilla."""
    conexion = conectar_bd()
    if not conexion: return None
    
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM npc WHERE id_npc = %s;", (id_npc,))
            n = cursor.fetchone()
            if not n: return None

            cursor.execute("""
                SELECT pa.nombre, pa.max_balas, COALESCE(string_agg(pr.descripcion, ' | '), '') as efecto
                FROM npc_armas na
                JOIN plantillas_armas pa ON na.id_plantilla = pa.id_plantilla
                LEFT JOIN armas_propiedades ap ON pa.id_plantilla = ap.id_plantilla
                LEFT JOIN propiedades_armas pr ON ap.id_propiedad = pr.id_propiedad
                WHERE na.id_npc = %s GROUP BY pa.nombre, pa.max_balas;
            """, (n['id_npc'],))
            
            dicc_armas = {
                arma['nombre']: {
                    "actual": arma['max_balas'], 
                    "max": arma['max_balas'],
                    "efecto": arma['efecto'] if arma['efecto'] else ""
                } for arma in cursor.fetchall()
            }

            cursor.execute("""
                SELECT b.nombre, b.descripcion FROM npc_buffos nb
                JOIN buffos b ON nb.id_buffo = b.id_buffo WHERE nb.id_npc = %s;
            """, (n['id_npc'],))
            
            lista_mejoras = [{"nombre": b["nombre"], "descripcion": b["descripcion"]} for b in cursor.fetchall()]

            npc_obj = Personaje(
                nombre=n['nombre'], max_hp=n['max_hp'], max_body_sp=n['max_body_sp'],
                max_head_sp=n['max_head_sp'], max_luck=0, move=n['max_move'],
                armas=dicc_armas, death_penalty=0, mejoras=lista_mejoras, 
                id_db=n['id_npc'], es_npc=True
            )
            
            npc_obj.hp = n['max_hp']
            npc_obj.body_sp = n['max_body_sp']
            npc_obj.head_sp = n['max_head_sp']
            npc_obj.move = n['max_move']
            
            return npc_obj
    except Exception as e:
        print(f"Error al instanciar NPC {id_npc}: {e}")
        return None
    finally:
        if conexion:
            conexion.close()
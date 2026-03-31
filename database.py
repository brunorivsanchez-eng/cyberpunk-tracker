import os
import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from dotenv import load_dotenv
from modelos import Personaje

# Carga de variables de entorno desde el archivo local .env
load_dotenv()

# ==============================================================================
# CONFIGURACIÓN DEL POOL DE CONEXIONES (Sustituye a conectar_bd)
# ==============================================================================
url_conexion = os.getenv("DATABASE_URL")

if not url_conexion:
    print("Error Crítico: Variable DATABASE_URL no encontrada en el entorno.")
    db_pool = None
else:
    # Creamos un pool global que mantiene conexiones activas en segundo plano.
    # row_factory=dict_row asegura que TODAS las filas regresen como diccionarios.
    db_pool = ConnectionPool(conninfo=url_conexion, min_size=1, max_size=10, kwargs={"row_factory": dict_row})

# ==============================================================================
# FUNCIONES DE BASE DE DATOS
# ==============================================================================

def cargar_partida_db():
    """Extrae el estado persistente de los jugadores desde PostgreSQL."""
    if not db_pool:
        return None, None

    pjs_cargados = []
    npcs_cargados = [] 

    try:
        # Usamos el pool de conexiones. Se cierra/devuelve automáticamente al salir del bloque 'with'
        with db_pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM jugadores;")
                filas_jugadores = cursor.fetchall()

                for j in filas_jugadores:
                    # NUEVA CONSULTA: Extrae datos del arma, sus propiedades y su tabla de distancias (VD)
                    cursor.execute("""
                        SELECT pa.nombre, ij.balas_actuales, pa.max_balas, 
                               pa.dados_dano, pa.id_dv_estandar, pa.id_dv_autofuego,
                               COALESCE(string_agg(pr.descripcion, ' | '), '') as efecto,
                               dv.dist_0_6m, dv.dist_7_12m, dv.dist_13_25m, dv.dist_26_50m, 
                               dv.dist_51_100m, dv.dist_101_200m, dv.dist_201_400m, dv.dist_401_800m
                        FROM inventario_jugadores ij
                        JOIN plantillas_armas pa ON ij.id_plantilla = pa.id_plantilla
                        LEFT JOIN armas_propiedades ap ON pa.id_plantilla = ap.id_plantilla
                        LEFT JOIN propiedades_armas pr ON ap.id_propiedad = pr.id_propiedad
                        LEFT JOIN dv_tablas dv ON pa.id_dv_estandar = dv.id_dv_tabla
                        WHERE ij.id_jugador = %s
                        GROUP BY pa.nombre, ij.balas_actuales, pa.max_balas, pa.dados_dano, pa.id_dv_estandar, pa.id_dv_autofuego,
                                 dv.dist_0_6m, dv.dist_7_12m, dv.dist_13_25m, dv.dist_26_50m, dv.dist_51_100m, dv.dist_101_200m, dv.dist_201_400m, dv.dist_401_800m;
                    """, (j['id_jugador'],))
                    
                    dicc_armas = {
                        arma['nombre']: {
                            "actual": arma['balas_actuales'],
                            "max": arma['max_balas'],
                            "dados_dano": arma['dados_dano'],
                            "dv_estandar": arma['id_dv_estandar'],
                            "dv_autofuego": arma['id_dv_autofuego'],
                            "efecto": arma['efecto'] if arma['efecto'] else "",
                            "dv_valores": [
                                arma['dist_0_6m'], arma['dist_7_12m'], arma['dist_13_25m'], 
                                arma['dist_26_50m'], arma['dist_51_100m'], arma['dist_101_200m'], 
                                arma['dist_201_400m'], arma['dist_401_800m']
                            ]
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
                    
                    cursor.execute("SELECT id_debufo FROM jugadores_debuffos WHERE id_jugador = %s;", (j['id_jugador'],))
                    pj.debufos_permanentes_ids = [d['id_debufo'] for d in cursor.fetchall()]
                    
                    pjs_cargados.append(pj)

    except Exception as e:
        print(f"Error Crítico al ejecutar consultas SQL: {e}")

    return pjs_cargados, npcs_cargados


def guardar_partida_db(pjs, npcs):
    """Persiste el estado dinámico de los jugadores en la base de datos."""
    if not db_pool:
        print("Error: Sin conexión al Pool. No se guardó la partida.")
        return

    try:
        with db_pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id_debufo FROM catalogo_debuffos WHERE nombre = '---';")
                ids_vacios = [row['id_debufo'] for row in cursor.fetchall()]

                for p in pjs:
                    if getattr(p, 'id_db', None) is None:
                        continue
                    
                    cursor.execute("""
                        UPDATE jugadores 
                        SET hp = %s, body_sp = %s, head_sp = %s, luck = %s, death_penalty = %s
                        WHERE id_jugador = %s;
                    """, (p.hp, p.body_sp, p.head_sp, p.luck, p.death_penalty, p.id_db))

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
        print(f"Falla Crítica durante transacción DML (UPDATE): {e}")


def cargar_catalogos_debuffos():
    """Extrae los catálogos de estados alterados (Temporal y Permanente)."""
    if not db_pool:
        cat_vacio = [{"nombre": "---", "descripcion": "Sin conexión", "tipo": "Temporal"}]
        return cat_vacio, cat_vacio

    try:
        with db_pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM catalogo_debuffos WHERE tipo = 'Temporal' ORDER BY id_debufo;")
                cat_temporales = cursor.fetchall()

                cursor.execute("SELECT * FROM catalogo_debuffos WHERE tipo = 'Permanente' ORDER BY id_debufo;")
                cat_permanentes = cursor.fetchall()
                
                return cat_temporales, cat_permanentes
    except Exception as e:
        print(f"Error Crítico al extraer catálogos de debuffos: {e}")
        return [], []


def obtener_bestiario_completo():
    """Extrae todos los NPCs con sus metadatos para el Dialogo del Bestiario."""
    if not db_pool: 
        return []
    
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id_npc, nombre, tier, faccion, max_hp, max_body_sp, max_head_sp, max_move,
                           base_combate, base_iniciativa
                    FROM npc 
                    ORDER BY tier ASC, faccion ASC, nombre ASC
                """)
                
                bestiario = []
                # Como el pool usa dict_row, fila ya es un diccionario garantizado
                for fila in cur.fetchall():
                    bestiario.append({
                        "id": fila['id_npc'],
                        "nombre": fila['nombre'],
                        "tier": fila['tier'],
                        "faccion": fila['faccion'],
                        "hp": fila['max_hp'],
                        "body": fila['max_body_sp'],
                        "head": fila['max_head_sp'],
                        "move": fila['max_move'],
                        "base_combate": fila['base_combate'],
                        "base_iniciativa": fila['base_iniciativa']
                    })
                return bestiario
    except Exception as e:
        print(f"Error al obtener bestiario: {repr(e)}") 
        return []


def instanciar_npc_dinamico(id_npc):
    """Construye un objeto Personaje aislado en memoria basado en una plantilla."""
    if not db_pool: 
        return None
    
    try:
        with db_pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM npc WHERE id_npc = %s;", (id_npc,))
                n = cursor.fetchone()
                if not n: return None

                # NUEVA CONSULTA NPCs: Extrae datos del arma, efecto y tabla de distancias (VD)
                cursor.execute("""
                    SELECT pa.nombre, pa.max_balas, pa.dados_dano, pa.id_dv_estandar, pa.id_dv_autofuego,
                           COALESCE(string_agg(pr.descripcion, ' | '), '') as efecto,
                           dv.dist_0_6m, dv.dist_7_12m, dv.dist_13_25m, dv.dist_26_50m, 
                           dv.dist_51_100m, dv.dist_101_200m, dv.dist_201_400m, dv.dist_401_800m
                    FROM npc_armas na
                    JOIN plantillas_armas pa ON na.id_plantilla = pa.id_plantilla
                    LEFT JOIN armas_propiedades ap ON pa.id_plantilla = ap.id_plantilla
                    LEFT JOIN propiedades_armas pr ON ap.id_propiedad = pr.id_propiedad
                    LEFT JOIN dv_tablas dv ON pa.id_dv_estandar = dv.id_dv_tabla
                    WHERE na.id_npc = %s 
                    GROUP BY pa.nombre, pa.max_balas, pa.dados_dano, pa.id_dv_estandar, pa.id_dv_autofuego,
                             dv.dist_0_6m, dv.dist_7_12m, dv.dist_13_25m, dv.dist_26_50m, dv.dist_51_100m, dv.dist_101_200m, dv.dist_201_400m, dv.dist_401_800m;
                """, (n['id_npc'],))
                
                dicc_armas = {
                    arma['nombre']: {
                        "actual": arma['max_balas'], 
                        "max": arma['max_balas'],
                        "dados_dano": arma['dados_dano'],
                        "dv_estandar": arma['id_dv_estandar'],
                        "dv_autofuego": arma['id_dv_autofuego'],
                        "efecto": arma['efecto'] if arma['efecto'] else "",
                        "dv_valores": [
                            arma['dist_0_6m'], arma['dist_7_12m'], arma['dist_13_25m'], 
                            arma['dist_26_50m'], arma['dist_51_100m'], arma['dist_101_200m'], 
                            arma['dist_201_400m'], arma['dist_401_800m']
                        ]
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
                
                npc_obj.base_combate = n['base_combate']
                npc_obj.base_iniciativa = n['base_iniciativa']
                
                return npc_obj
    except Exception as e:
        print(f"Error al instanciar NPC {id_npc}: {e}")
        return None
    
def cerrar_conexion_pool():
    """Cierra los workers del pool de NeonDB de forma segura al apagar la app."""
    if db_pool:
        db_pool.close()
        print("Pool de conexiones cerrado correctamente.")
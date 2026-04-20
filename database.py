import os
import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from dotenv import load_dotenv
from modelos import Personaje

# Carga de variables de entorno desde el archivo local .env
load_dotenv()

# ==============================================================================
# CONFIGURACIÓN DEL POOL DE CONEXIONES 
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
        with db_pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM jugadores;")
                filas_jugadores = cursor.fetchall()

                for j in filas_jugadores:
                    # Sin armas y sin death_penalty
                    pj = Personaje(
                        nombre=j['nombre'], max_hp=j['max_hp'], max_body_sp=j['max_body_sp'],
                        max_head_sp=j['max_head_sp'], max_luck=j['max_luck'], move=j['max_move'],
                        armas={}, id_db=j['id_jugador'], es_npc=False
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
                    
                    # 1. Guardar stats básicos (ELIMINADO death_penalty)
                    cursor.execute("""
                        UPDATE jugadores 
                        SET hp = %s, body_sp = %s, head_sp = %s, luck = %s
                        WHERE id_jugador = %s;
                    """, (p.hp, p.body_sp, p.head_sp, p.luck, p.id_db))
                    
                    # 2. Guardar debuffos permanentes
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


# ==============================================================================
# NUEVO SISTEMA: LISTAS DESPLEGABLES MODULARES Y VISTA PREVIA
# ==============================================================================

def obtener_lista_chasis():
    """Extrae TODOS los datos de los chasis base para la vista previa."""
    if not db_pool: return []
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                # CAMBIO: Usamos SELECT * para traer HP, SP, Move, etc.
                cur.execute("SELECT * FROM npc_base ORDER BY tier ASC, nombre ASC;")
                return cur.fetchall()
    except Exception as e:
        print(f"Error al obtener chasis: {repr(e)}") 
        return []

def obtener_lista_facciones():
    """Extrae las facciones disponibles."""
    if not db_pool: return []
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id_faccion, nombre FROM npc_faccion ORDER BY nombre ASC;")
                return cur.fetchall()
    except Exception as e:
        print(f"Error al obtener facciones: {repr(e)}") 
        return []

def obtener_preview_equipo(id_faccion, tier_exacto, rol_exacto):
    """Consulta rápida para previsualizar qué armas y cromo da una facción en un Tier y Rol específico."""
    if not db_pool: return [], []
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                # Buscar Armas filtrando por Tier Y Rol
                cur.execute("""
                    SELECT pa.nombre FROM faccion_armas fa
                    JOIN plantillas_armas pa ON fa.id_plantilla = pa.id_plantilla
                    WHERE fa.id_faccion = %s AND fa.tier_exacto = %s AND (fa.rol_requerido = 'Todos' OR fa.rol_requerido = %s);
                """, (id_faccion, tier_exacto, rol_exacto))
                armas = [row['nombre'] for row in cur.fetchall()]

                # Buscar Cromo filtrando por Tier Y Rol
                cur.execute("""
                    SELECT b.nombre FROM faccion_buffos fb
                    JOIN buffos b ON fb.id_buffo = b.id_buffo 
                    WHERE fb.id_faccion = %s AND fb.tier_exacto = %s AND (fb.rol_requerido = 'Todos' OR fb.rol_requerido = %s);
                """, (id_faccion, tier_exacto, rol_exacto))
                cromo = [row['nombre'] for row in cur.fetchall()]

                return armas, cromo
    except Exception as e:
        print(f"Error al obtener preview de equipo: {e}")
        return [], []
# ==============================================================================
# EL ENSAMBLADOR DE NPCs
# ==============================================================================

def instanciar_npc_dinamico(id_chasis, id_faccion):
    """Construye un NPC uniendo las Stats del Chasis con el Equipo de la Facción según el Tier y el Rol."""
    if not db_pool: 
        return None
    
    try:
        with db_pool.connection() as conexion:
            with conexion.cursor() as cursor:
                # 1. Traer los Stats del Chasis
                cursor.execute("SELECT * FROM npc_base WHERE id_base = %s;", (id_chasis,))
                chasis = cursor.fetchone()
                if not chasis: return None

                tier_npc = chasis['tier']
                rol_npc = chasis['rol']

                # 2. Traer el Nombre de la Facción
                cursor.execute("SELECT nombre FROM npc_faccion WHERE id_faccion = %s;", (id_faccion,))
                fac_db = cursor.fetchone()
                nombre_faccion = fac_db['nombre'] if fac_db else "Independiente"

                # Nombre compuesto final: ej. "Maelstrom (Veterano)"
                nombre_final = f"{nombre_faccion} ({chasis['nombre']})"

                # 3. Traer Armas de la Facción (Filtrando por Tier Y Rol)
                cursor.execute("""
                    SELECT pa.nombre, pa.dados_dano, pa.id_dv_estandar, pa.id_dv_autofuego,
                           COALESCE(string_agg(pr.descripcion, ' | '), '') as efecto,
                           dvs.dist_0_6m AS s_0_6, dvs.dist_7_12m AS s_7_12, dvs.dist_13_25m AS s_13_25, dvs.dist_26_50m AS s_26_50, 
                           dvs.dist_51_100m AS s_51_100, dvs.dist_101_200m AS s_101_200, dvs.dist_201_400m AS s_201_400, dvs.dist_401_800m AS s_401_800,
                           dva.dist_0_6m AS a_0_6, dva.dist_7_12m AS a_7_12, dva.dist_13_25m AS a_13_25, dva.dist_26_50m AS a_26_50, 
                           dva.dist_51_100m AS a_51_100, dva.dist_101_200m AS a_101_200, dva.dist_201_400m AS a_201_400, dva.dist_401_800m AS a_401_800
                    FROM faccion_armas fa
                    JOIN plantillas_armas pa ON fa.id_plantilla = pa.id_plantilla
                    LEFT JOIN armas_propiedades ap ON pa.id_plantilla = ap.id_plantilla
                    LEFT JOIN propiedades_armas pr ON ap.id_propiedad = pr.id_propiedad
                    LEFT JOIN dv_tablas dvs ON pa.id_dv_estandar = dvs.id_dv_tabla
                    LEFT JOIN dv_tablas dva ON pa.id_dv_autofuego = dva.id_dv_tabla
                    WHERE fa.id_faccion = %s AND fa.tier_exacto = %s AND (fa.rol_requerido = 'Todos' OR fa.rol_requerido = %s)
                    GROUP BY pa.nombre, pa.dados_dano, pa.id_dv_estandar, pa.id_dv_autofuego,
                             dvs.dist_0_6m, dvs.dist_7_12m, dvs.dist_13_25m, dvs.dist_26_50m, dvs.dist_51_100m, dvs.dist_101_200m, dvs.dist_201_400m, dvs.dist_401_800m,
                             dva.dist_0_6m, dva.dist_7_12m, dva.dist_13_25m, dva.dist_26_50m, dva.dist_51_100m, dva.dist_101_200m, dva.dist_201_400m, dva.dist_401_800m;
                """, (id_faccion, tier_npc, rol_npc))
                
                dicc_armas = {}
                for arma in cursor.fetchall():
                    dv_simple = [arma['s_0_6'], arma['s_7_12'], arma['s_13_25'], arma['s_26_50'], arma['s_51_100'], arma['s_101_200'], arma['s_201_400'], arma['s_401_800']]
                    dv_auto = [arma['a_0_6'], arma['a_7_12'], arma['a_13_25'], arma['a_26_50'], arma['a_51_100'], arma['a_101_200'], arma['a_201_400'], arma['a_401_800']]
                    
                    if all(v is None for v in dv_auto):
                        dv_auto = None
                        
                    dicc_armas[arma['nombre']] = {
                        "dados_dano": arma['dados_dano'],
                        "dv_estandar": arma['id_dv_estandar'],
                        "dv_autofuego": arma['id_dv_autofuego'],
                        "efecto": arma['efecto'] if arma['efecto'] else "",
                        "dv_valores": dv_simple,
                        "dv_valores_auto": dv_auto
                    }

                # 4. Traer Cromo de la Facción (Filtrando por Tier Y Rol)
                cursor.execute("""
                    SELECT b.nombre, b.descripcion 
                    FROM faccion_buffos fb
                    JOIN buffos b ON fb.id_buffo = b.id_buffo 
                    WHERE fb.id_faccion = %s AND fb.tier_exacto = %s AND (fb.rol_requerido = 'Todos' OR fb.rol_requerido = %s);
                """, (id_faccion, tier_npc, rol_npc))
                
                lista_mejoras = [{"nombre": b["nombre"], "descripcion": b["descripcion"]} for b in cursor.fetchall()]

                # 5. Instanciar el Objeto Personaje (Sin death_penalty)
                npc_obj = Personaje(
                    nombre=nombre_final, max_hp=chasis['max_hp'], max_body_sp=chasis['max_body_sp'],
                    max_head_sp=chasis['max_head_sp'], max_luck=0, move=chasis['max_move'],
                    armas=dicc_armas, mejoras=lista_mejoras, 
                    id_db=chasis['id_base'], es_npc=True
                )
                
                npc_obj.hp = chasis['max_hp']
                npc_obj.body_sp = chasis['max_body_sp']
                npc_obj.head_sp = chasis['max_head_sp']
                npc_obj.move = chasis['max_move']
                
                npc_obj.base_combate = chasis['base_combate']
                npc_obj.base_iniciativa = chasis['base_iniciativa']
                npc_obj.faccion = nombre_faccion
                
                return npc_obj
                
    except Exception as e:
        print(f"Error Crítico al instanciar NPC Ensamblado: {e}")
        return None
    
def cerrar_conexion_pool():
    """Cierra los workers del pool de NeonDB de forma segura al apagar la app."""
    if db_pool:
        db_pool.close()
        print("Pool de conexiones cerrado correctamente.")
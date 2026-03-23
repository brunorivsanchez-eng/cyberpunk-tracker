import os
import psycopg
from psycopg import OperationalError
from psycopg.rows import dict_row
from dotenv import load_dotenv
from modelos import Personaje

# Carga de variables de entorno desde el archivo local .env
load_dotenv()

# ==========================================
# GESTIÓN DE BASE DE DATOS POSTGRESQL
# ==========================================
def conectar_bd():
    """
    Establece y retorna la conexión a la base de datos NeonDB.
    Implementa manejo de errores y configura el retorno de diccionarios.
    """
    url_conexion = os.getenv("DATABASE_URL")
    
    if not url_conexion:
        print("Error Crítico: Variable DATABASE_URL no encontrada en el entorno.")
        return None

    try:
        # La conexión utiliza row_factory=dict_row para facilitar el mapeo de datos
        conexion = psycopg.connect(url_conexion, row_factory=dict_row)
        return conexion
    except OperationalError as e:
        print(f"Falla al conectar con la base de datos: {e}")
        return None
# ==========================================
# GESTIÓN VISUAL Y DE INTERFAZ
# ==========================================

def actualizar_color_hp(personaje_obj, dicc_widgets):
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)

    umbral_critico = personaje_obj.max_hp * 0.5
    es_npc = dicc_widgets.get("es_npc", False)

    if personaje_obj.hp <= umbral_critico:
        color_actual = "#FF0000"
    else:
        if es_npc:
            color_actual = "#9400D3"
        else:
            color_actual = "#15A315"

    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color_actual}; border-radius: 5px; }}"
        )

    if "nombre" in dicc_widgets:
        estilo_base = "font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: bold;"
        dicc_widgets["nombre"].setStyleSheet(f"color: {color_actual}; {estilo_base}")

# ==========================================
# LÓGICA DE COMBATE Y ATRIBUTOS
# ==========================================

def procesar_ataque(personaje_obj, entrada_widget, es_cabeza, es_melee, es_directo, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        danio = int(texto)
        personaje_obj.aplicar_impacto(danio, es_cabeza, es_melee, es_directo)
        
        for attr in ["hp", "body_sp", "head_sp"]:
            if attr in dicc_widgets:
                dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
        
        actualizar_color_hp(personaje_obj, dicc_widgets)
        entrada_widget.clear()

def procesar_curacion(personaje_obj, entrada_widget, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        cantidad = int(texto)
        personaje_obj.curar(cantidad)
        
        if "hp" in dicc_widgets:
            dicc_widgets["hp"].setValue(personaje_obj.hp)
            
        actualizar_color_hp(personaje_obj, dicc_widgets)
        entrada_widget.clear()

def ajustar_stat_secundario(personaje_obj, atributo, cantidad, barra_widget):
    personaje_obj.modificar_stat_secundario(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    barra_widget.setValue(nuevo_valor)

def ajustar_atributo_simple(personaje_obj, atributo, cantidad, label_widget):
    personaje_obj.modificar_atributo_simple(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    label_widget.setText(str(nuevo_valor))
    
def aplicar_dano_fijo(personaje_obj, cantidad, dicc_widgets):
    """Aplica daño directo al HP, ignorando armadura."""
    personaje_obj.aplicar_impacto(cantidad, es_cabeza=False, es_melee=False, es_directo=True)
    
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)
        
    actualizar_color_hp(personaje_obj, dicc_widgets)

# ==========================================
# LÓGICA DE ARMAMENTO
# ==========================================

def ajustar_municion_arma(personaje_obj, nombre_arma, cantidad, lbl_widget):
    """Ajusta munición asegurando los límites (0 a max)."""
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        nueva_municion = max(0, min(arma["actual"] + cantidad, arma["max"]))
        arma["actual"] = nueva_municion
        lbl_widget.setText(str(nueva_municion))

def recargar_arma_maxima(personaje_obj, nombre_arma, lbl_widget):
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        arma["actual"] = arma["max"]
        lbl_widget.setText(str(arma["actual"]))

# ==========================================
# CONTROL DE ESTADO
# ==========================================
    
def resetear_personaje(personaje_obj, dicc_widgets):
    """Restaura todos los atributos al máximo y actualiza la UI."""
    personaje_obj.hp = personaje_obj.max_hp
    personaje_obj.body_sp = personaje_obj.max_body_sp
    personaje_obj.head_sp = personaje_obj.max_head_sp
    personaje_obj.luck = personaje_obj.max_luck
    personaje_obj.move = personaje_obj.max_move
    personaje_obj.death_penalty = 0
    
    if hasattr(personaje_obj, 'max_bullets'):
        personaje_obj.bullets = personaje_obj.max_bullets

    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)
        actualizar_color_hp(personaje_obj, dicc_widgets)
        
    for attr in ["body_sp", "head_sp", "luck", "move"]:
        if attr in dicc_widgets:
            dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
            
    if hasattr(personaje_obj, "armas"):
        for nombre_arma, datos in personaje_obj.armas.items():
            datos["actual"] = datos["max"]
            if "armas" in dicc_widgets and nombre_arma in dicc_widgets["armas"]:
                dicc_widgets["armas"][nombre_arma].setText(str(datos["actual"]))
        
    if "death_penalty" in dicc_widgets:
        dicc_widgets["death_penalty"].setText(str(personaje_obj.death_penalty))
        
    if "debufos" in dicc_widgets:
        for combo in dicc_widgets["debufos"]:
            combo.setCurrentIndex(0) 

# ==========================================
# PERSISTENCIA DE DATOS (JSON)
# ==========================================

def cargar_partida_db():
    """
    Extrae los jugadores (estado dinámico) y los NPCs (plantillas estáticas)
    desde PostgreSQL y construye las listas de objetos Personaje.
    """
    conexion = conectar_bd()
    if not conexion:
        return None, None

    pjs_cargados = []
    npcs_cargados = []

    try:
        # --- 1. CARGA DE JUGADORES (Estado Dinámico) ---
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM jugadores;")
            filas_jugadores = cursor.fetchall()

            for j in filas_jugadores:
                # Consulta para obtener el inventario y concatenar múltiples propiedades
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
                
                armas_db = cursor.fetchall()
                dicc_armas = {}
                for arma in armas_db:
                    dicc_armas[arma['nombre']] = {
                        "actual": arma['balas_actuales'],
                        "max": arma['max_balas'],
                        "efecto": arma['efecto'] if arma['efecto'] else ""
                    }

                pj = Personaje(
                    nombre=j['nombre'], max_hp=j['max_hp'], max_body_sp=j['max_body_sp'],
                    max_head_sp=j['max_head_sp'], max_luck=j['max_luck'], move=j['max_move'],
                    armas=dicc_armas, death_penalty=j['death_penalty'], 
                    id_db=j['id_jugador'], es_npc=False
                )
                
                # Inyección del estado actual guardado en la BD
                pj.hp = j['hp']
                pj.body_sp = j['body_sp']
                pj.head_sp = j['head_sp']
                pj.luck = j['luck']
                pj.move = j['move']
                
                pjs_cargados.append(pj)

        # --- 2. CARGA DE NPCs (Plantillas Estáticas) ---
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM npc;")
            filas_npc = cursor.fetchall()

            for n in filas_npc:
                # Consulta de armas (Se asume que la plantilla inicia con cargador lleno)
                cursor.execute("""
                    SELECT pa.nombre, pa.max_balas,
                           COALESCE(string_agg(pr.descripcion, ' | '), '') as efecto
                    FROM npc_armas na
                    JOIN plantillas_armas pa ON na.id_plantilla = pa.id_plantilla
                    LEFT JOIN armas_propiedades ap ON pa.id_plantilla = ap.id_plantilla
                    LEFT JOIN propiedades_armas pr ON ap.id_propiedad = pr.id_propiedad
                    WHERE na.id_npc = %s
                    GROUP BY pa.nombre, pa.max_balas;
                """, (n['id_npc'],))
                
                armas_db = cursor.fetchall()
                dicc_armas = {}
                for arma in armas_db:
                    dicc_armas[arma['nombre']] = {
                        "actual": arma['max_balas'], 
                        "max": arma['max_balas'],
                        "efecto": arma['efecto'] if arma['efecto'] else ""
                    }

                # Consulta de Mejoras Cibernéticas / Buffos
                
                cursor.execute("""
                    SELECT b.nombre, b.descripcion 
                    FROM npc_buffos nb
                    JOIN buffos b ON nb.id_buffo = b.id_buffo
                    WHERE nb.id_npc = %s;
                """, (n['id_npc'],))
                
                buffos_db = cursor.fetchall()
                # CÓDIGO CORREGIDO: Construye una lista de diccionarios
                lista_mejoras = [{"nombre": b["nombre"], "descripcion": b["descripcion"]} for b in buffos_db]

                npc_obj = Personaje(
                    nombre=n['nombre'], max_hp=n['max_hp'], max_body_sp=n['max_body_sp'],
                    max_head_sp=n['max_head_sp'], max_luck=0, move=n['max_move'],
                    armas=dicc_armas, death_penalty=0, mejoras=lista_mejoras, 
                    id_db=n['id_npc'], es_npc=True
                )
                
                # Las plantillas siempre se instancian con la vida y armadura al máximo
                npc_obj.hp = n['max_hp']
                npc_obj.body_sp = n['max_body_sp']
                npc_obj.head_sp = n['max_head_sp']
                npc_obj.move = n['max_move']

                npcs_cargados.append(npc_obj)

    except Exception as e:
        print(f"Error Crítico al ejecutar consultas SQL: {e}")
    finally:
        conexion.close()

    return pjs_cargados, npcs_cargados

def guardar_partida_db(pjs, npcs):
    """
    Persiste el estado dinámico de los jugadores en PostgreSQL.
    Omite la lista de npcs por ser plantillas de solo lectura.
    """
    conexion = conectar_bd()
    if not conexion:
        print("Error: Imposible establecer conexión. No se guardó la partida.")
        return

    try:
        with conexion.cursor() as cursor:
            for p in pjs:
                # Verificación de integridad: Evita fallos si se inserta un objeto sin ID
                if getattr(p, 'id_db', None) is None:
                    print(f"Advertencia: Jugador '{p.nombre}' carece de id_db. Omisión de guardado.")
                    continue
                
                # 1. Actualización de Atributos Vitales
                cursor.execute("""
                    UPDATE jugadores 
                    SET hp = %s, body_sp = %s, head_sp = %s, 
                        luck = %s, move = %s, death_penalty = %s
                    WHERE id_jugador = %s;
                """, (p.hp, p.body_sp, p.head_sp, p.luck, p.move, p.death_penalty, p.id_db))

                # 2. Actualización de Munición
                # Se utiliza la cláusula FROM para emparejar el nombre del arma en memoria 
                # con su respectivo id_plantilla en la base de datos.
                if hasattr(p, "armas"):
                    for nombre_arma, datos in p.armas.items():
                        cursor.execute("""
                            UPDATE inventario_jugadores ij
                            SET balas_actuales = %s
                            FROM plantillas_armas pa
                            WHERE ij.id_plantilla = pa.id_plantilla
                              AND ij.id_jugador = %s
                              AND pa.nombre = %s;
                        """, (datos["actual"], p.id_db, nombre_arma))
            
            # Confirmación de la transacción completa
            conexion.commit()
            print("Estado de jugadores guardado exitosamente en NeonDB.")

    except Exception as e:
        # Reversión en caso de falla estructural
        conexion.rollback()
        print(f"Falla Crítica durante transacción DML (UPDATE): {e}")
    finally:
        conexion.close()